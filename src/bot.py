#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Video Yuklab Olish Boti
Ushbu bot foydalanuvchilarga URL manzilini yuborish orqali turli platformalardan videolarni yuklab olish imkonini beradi.
"""

import asyncio
import logging
import os
import re
import shutil
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

import aiofiles
import yt_dlp

# Deep Translator kutubxonasini import qilish
try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logging.getLogger(__name__).warning("Deep Translator kutubxonasi mavjud emas. Tarjima funksiyasi faol emas.")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# YouTube helper va Button handler import qilish
from src.youtube_helper import youtube_helper
from src.buttons import button_handler
from src.constants import (
    # Video cheklovlari
    MAX_VIDEO_SIZE,
    MAX_VIDEO_DURATION,
    DEFAULT_VIDEO_DURATION,
    # Telegram cheklovlari
    CAPTION_MAX_LENGTH,
    MESSAGE_MAX_LENGTH,
    # Fayl nomlari
    DOWNLOAD_DIR,
    DEFAULT_LOG_LEVEL,
    LOG_FILENAME,
    # Platforma ma'lumotlari
    PLATFORM_EMOJIS,
    PLATFORM_NAMES,
    PLATFORM_BUTTON_TEXTS,
    PLATFORM_EXAMPLE_URLS,
    MAIN_MENU_KEYBOARD,
    # Tarjima
    TRANSLATION_TARGET_LANG,
    TRANSLATION_TEXT_LIMIT,
    DESCRIPTION_PREVIEW_LENGTH,
    CAPTION_PREVIEW_LENGTH,
    # HTTP
    HTTP_TIMEOUT,
    SOCKET_TIMEOUT,
    REQUEST_RETRIES,
    FRAGMENT_RETRIES,
    # Health check
    HEALTH_CHECK_PORT,
    HEALTH_CHECK_HOST,
    # Messages
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    ABOUT_MESSAGE,
    YOUTUBE_BOT_ERROR_MESSAGE,
)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
logger = logging.getLogger(__name__)

# Jurnalni yoqish (Structured logging - fayl + console)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, DEFAULT_LOG_LEVEL),
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Agar yuklab olish katalogi mavjud bo'lmasa, yaratish
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


# =============================================================================
# RATE LIMITING
# =============================================================================
class RateLimiter:
    """Per-user rate limiting."""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, List[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, user_id: int) -> bool:
        """Check if user can make a request."""
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            # Remove old requests
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if req_time > cutoff
            ]
            
            # Check if limit reached
            if len(self.user_requests[user_id]) >= self.max_requests:
                return False
            
            # Add new request
            self.user_requests[user_id].append(now)
            return True
    
    def get_wait_time(self, user_id: int) -> float:
        """Get time until next request is allowed."""
        if not self.user_requests[user_id]:
            return 0
        
        oldest = min(self.user_requests[user_id])
        wait_until = oldest + timedelta(seconds=self.window_seconds)
        return max(0, (wait_until - datetime.now()).total_seconds())


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=5, window_seconds=60)


# =============================================================================
# COOKIE MANAGER (Class-based, not global variable)
# =============================================================================
class CookieManager:
    """Manage YouTube cookies securely."""
    
    def __init__(self):
        self._cached_path: Optional[str] = None
        self._cached_content: Optional[str] = None
    
    def get_path(self) -> Optional[str]:
        """Get cookies file path, creating if necessary."""
        if self._cached_path is not None:
            return self._cached_path

        cookies_content = os.getenv('COOKIES_CONTENT')
        if cookies_content:
            # Koyeb/Railway da \n literal bo'lib qolishi mumkin — tuzatish
            if '\\n' in cookies_content and '\n' not in cookies_content:
                cookies_content = cookies_content.replace('\\n', '\n')
            if '\\t' in cookies_content and '\t' not in cookies_content:
                cookies_content = cookies_content.replace('\\t', '\t')

            cookies_path = os.path.join(DOWNLOAD_DIR, 'cookies.txt')
            
            # Only write if content changed (optimization)
            if self._cached_content != cookies_content:
                try:
                    with open(cookies_path, 'w', encoding='utf-8') as f:
                        f.write(cookies_content)
                    logger.info(f"Cookies fayli yaratildi: {cookies_path}")
                    self._cached_content = cookies_content
                except Exception as e:
                    logger.error(f"Cookies faylini yaratishda xatolik: {str(e)}")
                    return None
            
            self._cached_path = cookies_path
            return cookies_path
        
        # Check for existing cookies file
        for path in ['cookies.txt', os.path.join(DOWNLOAD_DIR, 'cookies.txt')]:
            if os.path.exists(path):
                self._cached_path = path
                return path

        return None
    
    def validate_cookies(self) -> bool:
        """Validate cookies file format and expiration."""
        cookies_path = self.get_path()
        if not cookies_path or not os.path.exists(cookies_path):
            return False
        
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check Netscape format
            if not lines or not lines[0].startswith('#'):
                logger.warning("Cookies fayli Netscape formatda emas")
                return False
            
            # Check for essential YouTube cookies
            essential_cookies = {'LOGIN_INFO', 'SID', 'HSID'}
            found_cookies = set()
            
            for line in lines:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 6:
                    found_cookies.add(parts[5])
            
            if not essential_cookies.intersection(found_cookies):
                logger.warning("YouTube uchun muhim cookies topilmadi")
                return False
            
            logger.info(f"Cookies validation passed: {len(found_cookies)} cookies found")
            return True
            
        except Exception as e:
            logger.error(f"Cookies validation error: {str(e)}")
            return False


# Global cookie manager instance
cookie_manager = CookieManager()


# =============================================================================
# FILE LOCK MANAGER
# =============================================================================
class FileLockManager:
    """Manage file operation locks to prevent race conditions."""
    
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._main_lock = asyncio.Lock()
    
    async def get_lock(self, filename: str) -> asyncio.Lock:
        """Get or create a lock for a specific file."""
        async with self._main_lock:
            if filename not in self._locks:
                self._locks[filename] = asyncio.Lock()
            return self._locks[filename]
    
    async def remove_lock(self, filename: str):
        """Remove lock after file is deleted."""
        async with self._main_lock:
            if filename in self._locks:
                del self._locks[filename]


# Global file lock manager
file_lock_manager = FileLockManager()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def sanitize_url_for_logging(url: str) -> str:
    """Sanitize URL by removing sensitive query parameters."""
    try:
        parsed = urlparse(url)
        # Remove sensitive query params
        query_params = parse_qs(parsed.query)
        sensitive_params = {'token', 'key', 'secret', 'password', 'auth', 'session'}
        safe_params = {k: v for k, v in query_params.items() if k.lower() not in sensitive_params}
        
        # Rebuild URL
        from urllib.parse import urlencode
        safe_query = urlencode(safe_params, doseq=True)
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if safe_query:
            safe_url += f"?{safe_query}"
        return safe_url
    except Exception:
        return url[:100]  # Fallback: truncate


def validate_bot_token(token: str) -> bool:
    """Validate Telegram bot token format."""
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        return False
    
    # Telegram bot token format: digits:letters-underscores-dashes
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token))


def detect_platform(url: str) -> str:
    """URL manzilga qarab platformani aniqlash."""
    platforms = {
        'youtube': ['youtube.com', 'youtu.be'],
        'instagram': ['instagram.com', 'instagr.am'],
        'tiktok': ['tiktok.com'],
        'twitter': ['twitter.com', 'x.com'],
        'vimeo': ['vimeo.com'],
        'facebook': ['facebook.com', 'fb.com']
    }

    for platform, domains in platforms.items():
        for domain in domains:
            if domain in url:
                return platform
    return 'unknown'


def get_platform_sticker(platform: str) -> str:
    """Platformaga mos stiker qaytarish."""
    return PLATFORM_EMOJIS.get(platform, '❓')


def get_platform_button_text(platform: str) -> str:
    """Platformaga mos tugma matnini qaytarish."""
    return PLATFORM_BUTTON_TEXTS.get(platform, 'Video')


def check_ffmpeg_available() -> bool:
    """FFmpeg mavjudligini tekshirish."""
    return shutil.which('ffmpeg') is not None


def sanitize_filename(filename: str) -> str:
    """Fayl nomini tozalash - maxsus belgilarni olib tashlash."""
    clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    if len(clean_name) > 150:
        clean_name = clean_name[:150]
    return clean_name


async def extract_audio_from_video_async(video_path: str) -> Optional[str]:
    """Videodan audio ajratib olish (async version)."""
    if not check_ffmpeg_available():
        logger.warning("FFmpeg mavjud emas")
        return None

    try:
        audio_path = video_path.rsplit('.', 1)[0] + '_audio.mp3'
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-q:a', '0',
            '-map', 'a',
            '-y',
            audio_path
        ]
        
        # Use asyncio.create_subprocess_exec for non-blocking execution
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300
        )
        
        if process.returncode == 0 and os.path.exists(audio_path):
            return audio_path
        else:
            logger.error(f"Audio ajratishda xatolik: {stderr.decode()}")
            return None
            
    except asyncio.TimeoutError:
        logger.error("FFmpeg timeout: 300 seconds exceeded")
        return None
    except Exception as e:
        logger.error(f"Audio ajratishda istisno: {str(e)}")
        return None


def translate_text(text: str, target_lang: str = TRANSLATION_TARGET_LANG) -> str:
    """Matnni berilgan tilga tarjima qilish."""
    if not TRANSLATION_AVAILABLE or not text:
        return text

    try:
        if len(text) > TRANSLATION_TEXT_LIMIT:
            text = text[:TRANSLATION_TEXT_LIMIT]
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        logger.error(f"Tarjima xatosi: {str(e)}")
        return text


def is_valid_url(text: str) -> bool:
    """URL manzil haqiqiyligini tekshirish."""
    try:
        result = urlparse(text)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except ValueError:
        return False


def setup_cookies(ydl_opts: dict) -> None:
    """Cookies faylini opsiyalarga qo'shish."""
    cookies_path = cookie_manager.get_path()
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path


def setup_proxy(ydl_opts: dict) -> None:
    """Proxy sozlamalarini qo'shish."""
    proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    if proxy_url:
        ydl_opts['proxy'] = proxy_url


def get_base_ydl_opts(user_id: int) -> dict:
    """Barcha platformalar uchun asosiy yt-dlp opsiyalarini qaytarish."""
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{user_id}_%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'format': 'best[height<=720]/best[height<=480]/best',
        'noplaylist': True,
        'socket_timeout': SOCKET_TIMEOUT,
        'retries': REQUEST_RETRIES,
        'fragment_retries': FRAGMENT_RETRIES,
    }

    if check_ffmpeg_available():
        ydl_opts['prefer_ffmpeg'] = True
        ydl_opts['merge_output_format'] = 'mp4'

    setup_cookies(ydl_opts)
    setup_proxy(ydl_opts)

    return ydl_opts


def get_youtube_ydl_opts(user_id: int, url: str) -> dict:
    """YouTube uchun maxsus opsiyalarni qaytarish."""
    ydl_opts = youtube_helper.get_youtube_options(url)
    ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f'{user_id}_%(title)s.%(ext)s')
    ydl_opts['restrictfilenames'] = True

    if check_ffmpeg_available():
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'

    return ydl_opts


def get_instagram_ydl_opts(user_id: int) -> dict:
    """Instagram uchun maxsus opsiyalarni qaytarish."""
    ydl_opts = get_base_ydl_opts(user_id)
    ydl_opts['format'] = 'best[height<=720]/best[height<=480]/best'
    ydl_opts['writesubtitles'] = True
    ydl_opts['writeautomaticsub'] = True
    ydl_opts['subtitleslangs'] = ['en', 'ru', 'uz', 'all']
    return ydl_opts


# =============================================================================
# DOWNLOAD DIRECTORY CLEANUP
# =============================================================================
def cleanup_download_directory():
    """Clean up old files from download directory on startup."""
    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return
        
        max_age_hours = 24
        current_time = time.time()
        deleted_count = 0
        
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Cleanup: deleted old file {filename}")
        
        if deleted_count > 0:
            logger.info(f"Cleanup complete: {deleted_count} files deleted")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")


# =============================================================================
# TELEGRAM COMMAND HANDLERS
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fойдаланувчи /start buyrug'ini berganida xabar yuborish."""
    user = update.effective_user
    if not user or not update.message:
        if update.message:
            await update.message.reply_text("Foydalanuvchi ma'lumotlarini olish imkonsiz.")
        return

    welcome_message = WELCOME_MESSAGE.format(name=user.first_name)
    reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi /help buyrug'ini berganida xabar yuborish."""
    if update.message:
        await update.message.reply_text(HELP_MESSAGE)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchiga bot haqida ma'lumot yuborish."""
    if update.message:
        await update.message.reply_text(ABOUT_MESSAGE)


# =============================================================================
# CAPTION BUILDER
# =============================================================================

def build_caption(info_dict: dict, url: str, platform_sticker: str, platform_button_text: str) -> str:
    """Video uchun caption matnini yaratish."""
    video_title = info_dict.get('title', 'video')
    caption_text = f"{platform_sticker} {platform_button_text}: {video_title}"
    subtitle_info = ""

    is_instagram = 'instagram.com' in url or 'instagr.am' in url
    description = info_dict.get('description', '')

    if is_instagram and description:
        subtitle_info += "\n\n📢 Instagram Caption:\n"
        subtitle_info += description[:DESCRIPTION_PREVIEW_LENGTH] + ("..." if len(description) > DESCRIPTION_PREVIEW_LENGTH else "")

        if TRANSLATION_AVAILABLE:
            try:
                translated = translate_text(description, TRANSLATION_TARGET_LANG)
                if translated and translated != description:
                    subtitle_info += f"\n\n🔄 Tarjima:\n{translated[:DESCRIPTION_PREVIEW_LENGTH]}{'...' if len(translated) > DESCRIPTION_PREVIEW_LENGTH else ''}"
            except Exception as e:
                logger.error(f"Tarjima xatosi: {str(e)}")

    elif info_dict.get('subtitles') or info_dict.get('automatic_captions'):
        auto_captions = info_dict.get('automatic_captions', {})
        subtitles = info_dict.get('subtitles', {})

        if auto_captions:
            subtitle_info += "\n\n📢 🤖 Avtomatik titrlar mavjud\n"
        elif subtitles:
            subtitle_info += "\n\n📢 📝 Qo'lda titrlar mavjud\n"

        if TRANSLATION_AVAILABLE and description:
            try:
                translated = translate_text(description, TRANSLATION_TARGET_LANG)
                if translated and translated != description:
                    subtitle_info += f"\n🔄 Tarjima:\n{translated[:CAPTION_PREVIEW_LENGTH]}{'...' if len(translated) > CAPTION_PREVIEW_LENGTH else ''}"
            except Exception as e:
                logger.error(f"Tarjima xatosi: {str(e)}")

    elif description:
        subtitle_info += "\n\n📢 Video Description:\n"
        subtitle_info += description[:DESCRIPTION_PREVIEW_LENGTH] + ("..." if len(description) > DESCRIPTION_PREVIEW_LENGTH else "")

        if TRANSLATION_AVAILABLE:
            try:
                translated = translate_text(description, TRANSLATION_TARGET_LANG)
                if translated and translated != description:
                    subtitle_info += f"\n\n🔄 Tarjima:\n{translated[:DESCRIPTION_PREVIEW_LENGTH]}{'...' if len(translated) > DESCRIPTION_PREVIEW_LENGTH else ''}"
            except Exception as e:
                logger.error(f"Tarjima xatosi: {str(e)}")

    # Caption uzunligini tekshirish (Telegram limiti 1024 belgi) - QAT'IY
    if subtitle_info:
        total_length = len(caption_text + subtitle_info)
        if total_length <= CAPTION_MAX_LENGTH:
            caption_text += subtitle_info
        else:
            available_length = CAPTION_MAX_LENGTH - len(caption_text) - 3
            if available_length > 0:
                caption_text += subtitle_info[:available_length] + "..."
            else:
                caption_text = caption_text[:CAPTION_MAX_LENGTH - 3] + "..."

    # Yakuniy length check
    if len(caption_text) > CAPTION_MAX_LENGTH:
        caption_text = caption_text[:CAPTION_MAX_LENGTH - 3] + "..."

    return caption_text


# =============================================================================
# VIDEO DOWNLOAD HELPER FUNCTIONS
# =============================================================================

async def _validate_video_duration(info_dict: Optional[dict], progress_message) -> Tuple[Optional[dict], Optional[str]]:
    """Video davomiyligini tekshirish."""
    if info_dict is None:
        return None, "Video ma'lumotlarini olish imkonsiz."
    
    video_duration = info_dict.get('duration', 0) or 0
    max_duration = int(os.getenv("MAX_VIDEO_DURATION", str(DEFAULT_VIDEO_DURATION)))
    
    if video_duration and video_duration > max_duration:
        return None, f"Kechirasiz, men {max_duration // 60} daqiqadan ortiq videolarni yuklab ololmayman.\nVideo davomiyligi: {video_duration // 60} daqiqa"
    
    return info_dict, None


async def _validate_file_size(video_filename: Optional[str]) -> Tuple[int, Optional[str]]:
    """Fayl hajmini tekshirish."""
    if not video_filename or not os.path.exists(video_filename):
        return 0, "Fayl topilmadi."
    
    file_size = os.path.getsize(video_filename)
    
    if file_size > MAX_VIDEO_SIZE:
        return file_size, f"📹 Video fayl juda katta ({file_size / (1024*1024):.1f}MB).\nTelegram faqat {MAX_VIDEO_SIZE / (1024*1024):.0f}MB gacha fayllarni yuborishga ruxsat beradi."
    
    return file_size, None


async def _send_video_to_user(update: Update, video_filename: str, caption_text: str) -> None:
    """Videoni foydalanuvchiga yuborish (async file I/O)."""
    loop = asyncio.get_event_loop()
    
    # Use executor for file reading to avoid blocking
    with open(video_filename, 'rb') as video_file:
        await update.message.reply_video(
            video=video_file,
            caption=caption_text,
            supports_streaming=True
        )


async def _cleanup_file(video_filename: Optional[str]) -> None:
    """Yuklab olingan faylni tozalash (with lock)."""
    if not video_filename:
        return
    
    try:
        lock = await file_lock_manager.get_lock(video_filename)
        async with lock:
            if os.path.exists(video_filename):
                await asyncio.get_event_loop().run_in_executor(None, os.remove, video_filename)
                logger.info(f"Fayl tozalandi: {video_filename}")
                await file_lock_manager.remove_lock(video_filename)
    except Exception as e:
        logger.error(f"Faylni o'chirishda xatolik: {str(e)}")


async def _download_video_file(url: str, ydl_opts: dict, is_youtube: bool, progress_message) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
    """Download video file. Returns (info_dict, filename, error_message)."""
    try:
        if is_youtube:
            try:
                info_dict, video_filename = await youtube_helper.download_with_youtube_retry(
                    url, ydl_opts, progress_message
                )
                return info_dict, video_filename, None
            except yt_dlp.DownloadError as e:
                error_msg = str(e)
                logger.error(f"YouTube yuklab olishda xatolik: {error_msg}")
                if youtube_helper.is_youtube_bot_error(error_msg):
                    return None, None, YOUTUBE_BOT_ERROR_MESSAGE
                else:
                    return None, None, f"Kechirasiz, men YouTube videosini yuklab ololmadim.\nXato: {error_msg[:200]}"
            except Exception as e:
                logger.error(f"YouTube yuklab olishda kutilmagan xato: {str(e)}", exc_info=True)
                return None, None, f"Kechirasiz, YouTube videosini yuklab olishda xatolik yuz berdi.\nXato: {str(e)[:200]}"
        else:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Video yuklab olishga harakat qilinmoqda: {sanitize_url_for_logging(url)}")
                    info_dict = ydl.extract_info(url, download=True)
                    video_filename = ydl.prepare_filename(info_dict)
                    logger.info(f"Video muvaffaqiyatli yuklab olindi: {video_filename}")
                return info_dict, video_filename, None
            except yt_dlp.DownloadError as e:
                error_msg = str(e)
                logger.error(f"Yuklab olish xatosi: {error_msg}")
                if 'Unsupported URL' in error_msg:
                    return None, None, (
                        "Kechirasiz, men bu saytdan yuklab olishni qo'llab-quvvatlamayman.\n"
                        "Men YouTube, Vimeo, Twitter, Instagram, TikTok va minglab boshqa saytlarni qo'llab-quvvatlayman."
                    )
                else:
                    return None, None, f"Kechirasiz, men videoni yuklab ololmadim.\nXato: {error_msg[:200]}"
            except Exception as e:
                logger.error(f"Kutilmagan xato (yuklab olish): {str(e)}", exc_info=True)
                return None, None, f"Kechirasiz, videoni yuklab olishda xatolik yuz berdi.\nXato: {str(e)[:200]}"
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        return None, None, f"Kechirasiz, yuklab olishda xatolik yuz berdi.\nXato: {str(e)[:200]}"


# =============================================================================
# MAIN DOWNLOAD FUNCTION
# =============================================================================

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """URL manzildan video yuklab olish va foydalanuvchiga yuborish."""
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    user = update.effective_user

    if not user:
        await update.message.reply_text("Foydalanuvchi ma'lumotlarini olish imkonsiz.")
        return

    # Rate limiting check
    if not await rate_limiter.is_allowed(user.id):
        wait_time = rate_limiter.get_wait_time(user.id)
        await update.message.reply_text(
            f"⚠️ Juda ko'p so'rovlar! Iltimos, {wait_time:.0f} soniya kuting.\n"
            f"Siz {rate_limiter.max_requests} ta so'rovni {rate_limiter.window_seconds} soniyada yuborishingiz mumkin."
        )
        return

    # URL validation
    if not is_valid_url(url):
        await update.message.reply_text(
            "Menga video yuklab olish uchun haqiqiy URL manzil yuboring.\n\n"
            "Masalan: https://www.youtube.com/watch?v=example"
        )
        return

    # Log with sanitized URL
    sanitized_url = sanitize_url_for_logging(url)
    logger.info(f"Foydalanuvchi {user.first_name} ({user.id}) video so'radi: {sanitized_url}")

    platform = detect_platform(url)
    platform_sticker = get_platform_sticker(platform)
    platform_button_text = get_platform_button_text(platform)
    is_youtube = platform == 'youtube'

    progress_message = await update.message.reply_text(f"{platform_sticker} So'rovingiz qayta ishlanmoqda...")

    video_filename = None
    try:
        # Platformaga qarab opsiyalarni tanlash
        if is_youtube:
            ydl_opts = get_youtube_ydl_opts(user.id, url)
        else:
            ydl_opts = get_base_ydl_opts(user.id) if platform != 'instagram' else get_instagram_ydl_opts(user.id)

        # Video ma'lumotlarini olish
        await progress_message.edit_text(f"{platform_sticker} Video tahlil qilinmoqda...")

        info_opts = {'quiet': True, 'noplaylist': True}
        setup_cookies(info_opts)
        setup_proxy(info_opts)
        if is_youtube:
            info_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['tv', 'web'],
                }
            }
        
        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Video tahlil xatosi (user={user.id}, url={sanitized_url}): {error_msg}")
            if is_youtube and youtube_helper.is_youtube_bot_error(error_msg):
                await progress_message.edit_text(YOUTUBE_BOT_ERROR_MESSAGE)
            else:
                await progress_message.edit_text(f"Kechirasiz, men bu videoni tahlil qila olmadim.\nXato: {error_msg[:200]}")
            return
        except Exception as e:
            logger.error(f"Kutilmagan xato (tahlil, user={user.id}): {str(e)}", exc_info=True)
            await progress_message.edit_text(f"Kechirasiz, video tahlilida xatolik yuz berdi.\nXato: {str(e)[:200]}")
            return

        # Duration validation
        info_dict, duration_error = await _validate_video_duration(info_dict, progress_message)
        if duration_error:
            await progress_message.edit_text(duration_error)
            return

        # Video yuklab olish
        await progress_message.edit_text(f"{platform_sticker} Video yuklab olinmoqda...")
        info_dict, video_filename, download_error = await _download_video_file(
            url, ydl_opts, is_youtube, progress_message
        )
        
        if download_error:
            await progress_message.edit_text(download_error)
            await _cleanup_file(video_filename)
            return

        # Validate info_dict after download
        if info_dict is None:
            await progress_message.edit_text("Kechirasiz, video ma'lumotlarini olish imkonsiz.")
            await _cleanup_file(video_filename)
            return

        # Filename sanitization before further processing
        if video_filename and os.path.exists(video_filename):
            dir_name = os.path.dirname(video_filename)
            base_name = os.path.basename(video_filename)
            name, ext = os.path.splitext(base_name)
            clean_name = sanitize_filename(name)
            clean_filename = os.path.join(dir_name, f"{clean_name}{ext}")

            if clean_filename != video_filename:
                try:
                    # Check if target filename already exists
                    if os.path.exists(clean_filename):
                        # Add timestamp to avoid conflict
                        timestamp = int(time.time())
                        clean_filename = os.path.join(dir_name, f"{clean_name}_{timestamp}{ext}")
                    
                    os.rename(video_filename, clean_filename)
                    video_filename = clean_filename
                    logger.info(f"Fayl nomi tozalandi: {clean_filename}")
                except Exception as e:
                    logger.error(f"Fayl nomini tozalashda xatolik: {str(e)}")

        # File size validation
        file_size, size_error = await _validate_file_size(video_filename)
        if size_error:
            await progress_message.edit_text(size_error)
            await _cleanup_file(video_filename)
            return

        # Send video to user
        caption_text = build_caption(info_dict, url, platform_sticker, platform_button_text)
        
        try:
            await progress_message.edit_text(f"{platform_sticker} Video Telegramga yuklanmoqda...")
            await _send_video_to_user(update, video_filename, caption_text)
        except Exception as e:
            logger.error(f"Video yuborishda xatolik (user={user.id}): {str(e)}", exc_info=True)
            await progress_message.edit_text(f"Kechirasiz, videoni yuborishda xatolik yuz berdi.\nXato: {str(e)[:200]}")
            await _cleanup_file(video_filename)
            return

        # Delete progress message
        try:
            await progress_message.delete()
        except Exception as e:
            logger.warning(f"Progress xabarni o'chirib bo'lmadi: {str(e)}")

    except Exception as e:
        logger.error(f"Kutilmagan xato (user={user.id}): {str(e)}", exc_info=True)
        try:
            await progress_message.edit_text(f"Kechirasiz, kutilmagan xato yuz berdi.\nXato: {str(e)[:200]}")
        except Exception:
            pass
    finally:
        # Faylni har doim tozalash
        await _cleanup_file(video_filename)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kiruvchi xabarlarni qayta ishlash."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user

    if not user:
        logger.warning("Foydalanuvchi ma'lumotlari yo'q")
        return

    user_name = user.first_name if user else "Noma'lum"
    logger.info(f"Foydalanuvchi {user_name} ({user.id}) xabar yubordi: {text[:100]}")

    if is_valid_url(text):
        await download_video(update, context)
    else:
        await update.message.reply_text(
            "Menga video yuklab olish uchun haqiqiy URL manzil yuboring.\n\n"
            "Masalan: https://www.youtube.com/watch?v=example"
        )


# =============================================================================
# HEALTH CHECK SERVER
# =============================================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Koyeb health check uchun sodda HTTP handler."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        pass  # Loglarni yashirish


def start_health_server():
    """Koyeb uchun health check HTTP serverni background threadda ishga tushirish."""
    port = int(os.getenv('PORT', str(HEALTH_CHECK_PORT)))
    server = HTTPServer((HEALTH_CHECK_HOST, port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health check server port {port} da ishga tushdi")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main() -> None:
    """Botni ishga tushirish."""
    logger.info("Bot ishga tushirilmoqda...")
    
    # Koyeb health check serverini ishga tushirish
    start_health_server()
    
    # Download directory cleanup
    cleanup_download_directory()
    
    # Validate bot token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_BOT_TOKEN = "".join(char for char in TELEGRAM_BOT_TOKEN if ord(char) > 32)

    if not validate_bot_token(TELEGRAM_BOT_TOKEN):
        logger.error("TELEGRAM_BOT_TOKEN .env faylida sozlanmagan yoki noto'g'ri formatda!")
        print("Xato: TELEGRAM_BOT_TOKEN .env faylida sozlanmagan yoki noto'g'ri formatda!")
        print("Iltimos, .env faylini tahrirlang va haqiqiy bot tokenini kiriting.")
        print("Token formati: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        return

    # Validate cookies if provided
    if os.getenv('COOKIES_CONTENT'):
        if cookie_manager.validate_cookies():
            logger.info("YouTube cookies validation passed")
        else:
            logger.warning("YouTube cookies validation failed - may encounter bot detection")

    # Check FFmpeg
    if not check_ffmpeg_available():
        logger.warning("FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        print("⚠️  FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        print("💡 FFmpeg ni o'rnatish uchun:")
        print("   Windows: https://ffmpeg.org/download.html dan yuklab oling")
        print("   MacOS: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")

    # Build application with proper configuration
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).request_timeout(HTTP_TIMEOUT).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishga tushirilmoqda...")
    logger.info("Bot polling boshlandi")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n🔄 Bot o'chirilmoqda...")
        logger.info("Bot KeyboardInterrupt orqali o'chirildi")
        print("✅ Bot to'g'ri o'chirildi")
    except Exception as e:
        logger.error(f"Bot ishga tushirishda xatolik: {e}", exc_info=True)
        print(f"❌ Bot ishga tushirishda xatolik: {e}")


if __name__ == '__main__':
    main()
