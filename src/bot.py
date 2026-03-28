#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Video Yuklab Olish Boti
Ushbu bot foydalanuvchilarga URL manzilini yuborish orqali turli platformalardan videolarni yuklab olish imkonini beradi.
"""

import logging
import os
import re
import shutil
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

import yt_dlp

# Deep Translator kutubxonasini import qilish
try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Deep Translator kutubxonasi mavjud emas. Tarjima funksiyasi faol emas.")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# YouTube helper va Button handler import qilish
from src.youtube_helper import youtube_helper
from src.buttons import button_handler

# Jurnalni yoqish
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Agar yuklab olish katalogi mavjud bo'lmasa, yaratish
DOWNLOADS_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)


def detect_platform(url):
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


def get_platform_sticker(platform):
    """Platformaga mos stiker qaytarish."""
    stickers = {
        'youtube': '🔴',
        'instagram': '📸',
        'tiktok': '🎵',
        'twitter': '🐦',
        'vimeo': '🔷',
        'facebook': '📘',
        'unknown': '❓'
    }
    return stickers.get(platform, '❓')


def get_platform_button_text(platform):
    """Platformaga mos tugma matnini qaytarish."""
    buttons = {
        'youtube': 'YouTube Videosi',
        'instagram': 'Instagram Videosi',
        'tiktok': 'TikTok Videosi',
        'twitter': 'Twitter Videosi',
        'vimeo': 'Vimeo Videosi',
        'facebook': 'Facebook Videosi',
        'unknown': 'Boshqa Video'
    }
    return buttons.get(platform, 'Video')


def check_ffmpeg_available():
    """FFmpeg mavjudligini tekshirish."""
    return shutil.which('ffmpeg') is not None


def sanitize_filename(filename):
    """Fayl nomini tozalash - maxsus belgilarni olib tashlash."""
    clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    if len(clean_name) > 150:
        clean_name = clean_name[:150]
    return clean_name


def extract_audio_from_video(video_path):
    """Videodan audio ajratib olish."""
    if not check_ffmpeg_available():
        return None

    try:
        import subprocess
        audio_path = video_path.rsplit('.', 1)[0] + '_audio.mp3'
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-q:a', '0',
            '-map', 'a',
            '-y',
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and os.path.exists(audio_path):
            return audio_path
        else:
            logger.error(f"Audio ajratishda xatolik: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Audio ajratishda istisno: {str(e)}")
        return None


def translate_text(text, target_lang='uz'):
    """Matnni berilgan tilga tarjima qilish."""
    if not TRANSLATION_AVAILABLE or not text:
        return text

    try:
        if len(text) > 5000:
            text = text[:5000]
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        logger.error(f"Tarjima xatosi: {str(e)}")
        return text


def is_valid_url(text):
    """URL manzil haqiqiyligini tekshirish."""
    try:
        result = urlparse(text)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except ValueError:
        return False


def setup_cookies(ydl_opts):
    """Cookies faylini opsiyalarga qo'shish (bir joyda markazlashtirilgan)."""
    cookies_content = os.getenv('COOKIES_CONTENT')
    if cookies_content:
        cookies_path = os.path.join(DOWNLOADS_DIR, 'cookies.txt')
        try:
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write(cookies_content)
            ydl_opts['cookiefile'] = cookies_path
            logger.info(f"Cookies fayli yaratildi: {cookies_path}")
        except Exception as e:
            logger.error(f"Cookies faylini yaratishda xatolik: {str(e)}")
    elif os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    elif os.path.exists(os.path.join(DOWNLOADS_DIR, 'cookies.txt')):
        ydl_opts['cookiefile'] = os.path.join(DOWNLOADS_DIR, 'cookies.txt')


def setup_proxy(ydl_opts):
    """Proxy sozlamalarini qo'shish (bir joyda markazlashtirilgan)."""
    proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    if proxy_url:
        ydl_opts['proxy'] = proxy_url


def get_base_ydl_opts(user_id):
    """Barcha platformalar uchun asosiy yt-dlp opsiyalarini qaytarish."""
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOADS_DIR, f'{user_id}_%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'format': 'best[height<=720]/best[height<=480]/best',
        'noplaylist': True,
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
    }

    if check_ffmpeg_available():
        ydl_opts['prefer_ffmpeg'] = True
        ydl_opts['merge_output_format'] = 'mp4'

    setup_cookies(ydl_opts)
    setup_proxy(ydl_opts)

    return ydl_opts


def get_youtube_ydl_opts(user_id, url):
    """YouTube uchun maxsus opsiyalarni qaytarish."""
    ydl_opts = youtube_helper.get_youtube_options(url)
    # outtmpl ni qo'shish (youtube_helper da yo'q)
    ydl_opts['outtmpl'] = os.path.join(DOWNLOADS_DIR, f'{user_id}_%(title)s.%(ext)s')
    ydl_opts['restrictfilenames'] = True

    if check_ffmpeg_available():
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'

    return ydl_opts


def get_instagram_ydl_opts(user_id):
    """Instagram uchun maxsus opsiyalarni qaytarish."""
    ydl_opts = get_base_ydl_opts(user_id)
    ydl_opts['format'] = 'best[height<=720]/best[height<=480]/best'
    ydl_opts['writesubtitles'] = True
    ydl_opts['writeautomaticsub'] = True
    ydl_opts['subtitleslangs'] = ['en', 'ru', 'uz', 'all']
    return ydl_opts


async def send_instagram_content_separately(update, video_filename, info_dict, platform_sticker, platform_button_text):
    """Instagram video va audioni alohida yuborish."""
    video_title = info_dict.get('title', 'Instagram video')

    with open(video_filename, 'rb') as video_file:
        caption_text = f"{platform_sticker} {platform_button_text} (Video): {video_title}"

        if info_dict.get('description'):
            instagram_caption = info_dict.get('description', '')
            if len(instagram_caption) > 200:
                caption_text += f"\n\n📢 Caption:\n{instagram_caption[:200]}..."
            else:
                caption_text += f"\n\n📢 Caption:\n{instagram_caption}"

            if TRANSLATION_AVAILABLE:
                try:
                    translated_caption = translate_text(instagram_caption, 'uz')
                    if translated_caption and translated_caption != instagram_caption:
                        caption_text += f"\n\n🔄 Tarjima:\n{translated_caption[:200]}{'...' if len(translated_caption) > 200 else ''}"
                except Exception as e:
                    logger.error(f"Tarjima xatosi: {str(e)}")

        await update.message.reply_video(
            video=video_file,
            caption=caption_text,
            supports_streaming=True
        )

    if check_ffmpeg_available():
        await update.message.reply_text("🎵 Audioni ajratish jarayoni boshlanmoqda...")

        audio_path = extract_audio_from_video(video_filename)
        if audio_path and os.path.exists(audio_path):
            audio_size = os.path.getsize(audio_path)
            max_size = int(os.getenv("MAX_VIDEO_SIZE", "52428800"))

            if audio_size <= max_size:
                with open(audio_path, 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=f"{video_title} (Audio)",
                        caption=f"{platform_sticker} {platform_button_text} (Audio): {video_title}"
                    )
            else:
                await update.message.reply_text(
                    f"❌ Audio fayl juda katta ({audio_size / (1024*1024):.1f}MB). "
                    f"Telegram faqat {max_size / (1024*1024):.0f}MB gacha fayllarni yuborishga ruxsat beradi."
                )
            # Audio faylni tozalash
            try:
                os.remove(audio_path)
            except Exception:
                pass
        else:
            await update.message.reply_text("❌ Audioni ajratishda xatolik yuz berdi.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi /start buyrug'ini berganida xabar yuborish."""
    user = update.effective_user
    if not user or not update.message:
        if update.message:
            await update.message.reply_text("Foydalanuvchi ma'lumotlarini olish imkonsiz.")
        return

    welcome_message = (
        f"👋 Salom {user.first_name}!\n\n"
        "Men turli platformalardan videolarni yuklab olishga yordam beradigan ilg'or video botman.\n\n"
        "📥 Menga video URL manzilini yuboring va men uni siz uchun yuklab olaman.\n"
        "✅ Qo'llab-quvvatlanadigan platformalar:\n"
        "• 🟥 YouTube\n"
        "• 📸 Instagram\n"
        "• 🎵 TikTok\n"
        "• 🐦 Twitter/X\n"
        "• 🔷 Vimeo\n"
        "• 📘 Facebook\n\n"
        "⚠️ Eslatma: Telegram cheklovlari tufayli 50MB dan katta videolar maxsus usullar bilan yuboriladi.\n\n"
        "👨‍💻 Muallif: N.Damir - Senior Dasturchi"
    )

    keyboard = [
        [InlineKeyboardButton("🔴 YouTube", callback_data="platform_youtube")],
        [InlineKeyboardButton("📸 Instagram", callback_data="platform_instagram")],
        [InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok")],
        [InlineKeyboardButton("🐦 Twitter", callback_data="platform_twitter")],
        [InlineKeyboardButton("🔷 Vimeo", callback_data="platform_vimeo")],
        [InlineKeyboardButton("📘 Facebook", callback_data="platform_facebook")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi /help buyrug'ini berganida xabar yuborish."""
    help_text = (
        "🤖 Video Yuklab Olish Boti Yordami\n\n"
        "Men sizga turli platformalardan videolarni yuklab olishga yordam beraman.\n\n"
        "📥 Foydalanish bo'yicha qo'llanma:\n"
        "1. Menga yuklab olmoqchi bo'lgan videoning URL manzilini yuboring.\n"
        "2. Men uni qayta ishlab, videoni qaytaraman.\n\n"
        "📋 Qo'llab-quvvatlanadigan platformalar:\n"
        "• 🟥 YouTube\n"
        "• 📸 Instagram\n"
        "• 🎵 TikTok\n"
        "• 🐦 Twitter/X\n"
        "• 🔷 Vimeo\n"
        "• 📘 Facebook\n\n"
        "⚠️ Cheklovlar:\n"
        "• 100 daqiqadan ortiq videolarni yuklab olib bo'lmaydi.\n"
        "• 50MB dan katta videolar maxsus usullar bilan yuboriladi.\n"
        "• Ba'zi saytlar yuklab olishni cheklaydi.\n\n"
        "⌨️ Buyruqlar:\n"
        "/start - Botni ishga tushirish\n"
        "/help - Ushbu yordam xabarini ko'rsatish\n"
        "/about - Bot haqida ma'lumot ko'rsatish"
    )
    if update.message:
        await update.message.reply_text(help_text)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchiga bot haqida ma'lumot yuborish."""
    about_text = (
        "📹 Video Yuklab Olish Boti\n\n"
        "Ushbu bot sizga turli platformalardan videolarni bevosita Telegramga yuklab olish imkonini beradi.\n\n"
        "🛠 Foydalanilgan texnologiyalar:\n"
        "• 🐍 python-telegram-bot\n"
        "• 📥 yt-dlp\n"
        "• 🌐 deep-translator (tarjima uchun)\n\n"
        "👨‍💻 Dasturchi:\n"
        "N.Damir - Senior Dasturchi\n\n"
        "🔒 Maxfiylik:\n"
        "Hech qanday video yoki shaxsiy ma'lumot serverlarimizda saqlanmaydi.\n"
        "Barcha qayta ishlash vaqtinchalik amalga oshiriladi va fayllar yuborilgandan keyin o'chirib tashlanadi."
    )
    if update.message:
        await update.message.reply_text(about_text)


def build_caption(info_dict, url, platform_sticker, platform_button_text):
    """Video uchun caption matnini yaratish."""
    video_title = info_dict.get('title', 'video')
    caption_text = f"{platform_sticker} {platform_button_text}: {video_title}"
    subtitle_info = ""

    is_instagram = 'instagram.com' in url or 'instagr.am' in url
    description = info_dict.get('description', '')

    if is_instagram and description:
        subtitle_info += "\n\n📢 Instagram Caption:\n"
        subtitle_info += description[:300] + ("..." if len(description) > 300 else "")

        if TRANSLATION_AVAILABLE:
            try:
                translated = translate_text(description, 'uz')
                if translated and translated != description:
                    subtitle_info += f"\n\n🔄 Tarjima:\n{translated[:300]}{'...' if len(translated) > 300 else ''}"
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
                translated = translate_text(description, 'uz')
                if translated and translated != description:
                    subtitle_info += f"\n🔄 Tarjima:\n{translated[:200]}{'...' if len(translated) > 200 else ''}"
            except Exception as e:
                logger.error(f"Tarjima xatosi: {str(e)}")

    elif description:
        subtitle_info += "\n\n📢 Video Description:\n"
        subtitle_info += description[:300] + ("..." if len(description) > 300 else "")

        if TRANSLATION_AVAILABLE:
            try:
                translated = translate_text(description, 'uz')
                if translated and translated != description:
                    subtitle_info += f"\n\n🔄 Tarjima:\n{translated[:300]}{'...' if len(translated) > 300 else ''}"
            except Exception as e:
                logger.error(f"Tarjima xatosi: {str(e)}")

    # Caption uzunligini tekshirish (Telegram limiti 1024 belgi)
    if subtitle_info:
        if len(caption_text + subtitle_info) <= 1024:
            caption_text += subtitle_info
        else:
            available_length = 1024 - len(caption_text) - 50
            if available_length > 100:
                caption_text += subtitle_info[:available_length] + "..."

    return caption_text


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """URL manzildan video yuklab olish va foydalanuvchiga yuborish."""
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    user = update.effective_user

    if not user:
        await update.message.reply_text("Foydalanuvchi ma'lumotlarini olish imkonsiz.")
        return

    logger.info(f"Foydalanuvchi {user.first_name} ({user.id}) quyidagi uchun yuklab olishni so'radi: {url}")

    platform = detect_platform(url)
    platform_sticker = get_platform_sticker(platform)
    platform_button_text = get_platform_button_text(platform)
    is_youtube = platform == 'youtube'
    is_instagram = platform == 'instagram'

    progress_message = await update.message.reply_text(f"{platform_sticker} So'rovingiz qayta ishlanmoqda...")

    video_filename = None
    try:
        # Platformaga qarab opsiyalarni tanlash
        if is_youtube:
            ydl_opts = get_youtube_ydl_opts(user.id, url)
        elif is_instagram:
            ydl_opts = get_instagram_ydl_opts(user.id)
        else:
            ydl_opts = get_base_ydl_opts(user.id)

        # Avval video ma'lumotlarini olish
        await progress_message.edit_text(f"{platform_sticker} Video tahlil qilinmoqda...")

        # Info olish uchun ham cookies va YouTube sozlamalarini ishlatish
        info_opts = {'quiet': True, 'noplaylist': True}
        setup_cookies(info_opts)
        setup_proxy(info_opts)
        if is_youtube:
            info_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['mweb', 'android'],
                }
            }
        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                if info_dict is None:
                    await progress_message.edit_text(
                        "Kechirasiz, men bu videoni tahlil qila olmadim.\n"
                        "Iltimos, URL manzil to'g'ri ekanligini tekshiring."
                    )
                    return

                video_duration = info_dict.get('duration', 0)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Video tahlil xatosi: {error_msg}")
            if is_youtube and youtube_helper.is_youtube_bot_error(error_msg):
                await progress_message.edit_text(youtube_helper.get_youtube_error_message())
            else:
                await progress_message.edit_text(
                    f"Kechirasiz, men bu videoni tahlil qila olmadim.\n"
                    f"Xato: {error_msg[:200]}"
                )
            return

        # Video davomiyligini tekshirish
        max_duration = int(os.getenv("MAX_VIDEO_DURATION", "6000"))
        if max_duration == 600:
            max_duration = 6000

        if video_duration and video_duration > max_duration:
            await progress_message.edit_text(
                f"Kechirasiz, men {max_duration // 60} daqiqadan ortiq videolarni yuklab ololmayman.\n"
                f"Video davomiyligi: {video_duration // 60} daqiqa"
            )
            return

        # Video yuklab olish
        await progress_message.edit_text(f"{platform_sticker} Video yuklab olinmoqda...")

        if is_youtube:
            try:
                info_dict, video_filename = await youtube_helper.download_with_youtube_retry(url, ydl_opts, progress_message)
            except Exception as e:
                logger.error(f"YouTube yuklab olishda xatolik: {str(e)}")
                error_msg = str(e).lower()
                if youtube_helper.is_youtube_bot_error(error_msg):
                    await progress_message.edit_text(youtube_helper.get_youtube_error_message())
                else:
                    await progress_message.edit_text(
                        f"Kechirasiz, men YouTube videosini yuklab ololmadim.\n"
                        f"Xato: {str(e)[:200]}"
                    )
                return
        else:
            # Boshqa platformalar uchun oddiy yuklab olish
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Video yuklab olishga harakat qilinmoqda: {url}")
                    info_dict = ydl.extract_info(url, download=True)
                    video_filename = ydl.prepare_filename(info_dict)
                    logger.info(f"Video muvaffaqiyatli yuklab olindi: {video_filename}")
            except yt_dlp.DownloadError as e:
                logger.error(f"Yuklab olish xatosi: {str(e)}")
                error_msg = str(e)
                if 'Unsupported URL' in error_msg:
                    await progress_message.edit_text(
                        "Kechirasiz, men bu saytdan yuklab olishni qo'llab-quvvatlamayman.\n"
                        "Men YouTube, Vimeo, Twitter, Instagram, TikTok va minglab boshqa saytlarni qo'llab-quvvatlayman."
                    )
                else:
                    await progress_message.edit_text(
                        f"Kechirasiz, men videoni yuklab ololmadim.\n"
                        f"Xato: {error_msg[:200]}"
                    )
                return

        # Fayl nomini tozalash
        if video_filename and os.path.exists(video_filename):
            dir_name = os.path.dirname(video_filename)
            base_name = os.path.basename(video_filename)
            name, ext = os.path.splitext(base_name)
            clean_name = sanitize_filename(name)
            clean_filename = os.path.join(dir_name, f"{clean_name}{ext}")

            if clean_filename != video_filename:
                try:
                    os.rename(video_filename, clean_filename)
                    video_filename = clean_filename
                except Exception as e:
                    logger.error(f"Fayl nomini tozalashda xatolik: {str(e)}")

        # Fayl mavjudligini tekshirish
        if not video_filename or not os.path.exists(video_filename):
            await progress_message.edit_text(
                "Kechirasiz, men videoni yuklab ololmadim.\n"
                "Fayl yaratilmadi."
            )
            return

        # Fayl hajmini tekshirish
        file_size = os.path.getsize(video_filename)
        max_size = int(os.getenv("MAX_VIDEO_SIZE", "52428800"))  # 50MB

        if file_size > max_size:
            await progress_message.edit_text(
                f"📹 Video fayl juda katta ({file_size / (1024*1024):.1f}MB).\n"
                f"Telegram faqat {max_size / (1024*1024):.0f}MB gacha fayllarni yuborishga ruxsat beradi."
            )
            return

        # Foydalanuvchiga video yuborish
        await progress_message.edit_text(f"{platform_sticker} Video Telegramga yuklanmoqda...")

        caption_text = build_caption(info_dict, url, platform_sticker, platform_button_text)

        with open(video_filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=caption_text,
                supports_streaming=True
            )

        # Progress xabarni o'chirish
        try:
            await progress_message.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Kutilmagan xato: {str(e)}")
        try:
            await progress_message.edit_text(
                f"Kechirasiz, kutilmagan xato yuz berdi.\n"
                f"Xato: {str(e)[:200]}"
            )
        except Exception:
            pass
    finally:
        # Yuklab olingan faylni har doim tozalash
        if video_filename and os.path.exists(video_filename):
            try:
                os.remove(video_filename)
            except Exception:
                pass


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kiruvchi xabarlarni qayta ishlash."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user

    user_name = user.first_name if user else "Noma'lum"
    logger.info(f"Foydalanuvchi {user_name} yubordi: {text}")

    if is_valid_url(text):
        await download_video(update, context)
    else:
        await update.message.reply_text(
            "Menga video yuklab olish uchun haqiqiy URL manzil yuboring.\n\n"
            "Masalan: https://www.youtube.com/watch?v=example"
        )


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
    port = int(os.getenv('PORT', '8000'))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health check server port {port} da ishga tushdi")


def main() -> None:
    """Botni ishga tushirish."""
    # Koyeb health check serverini ishga tushirish
    start_health_server()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_BOT_TOKEN = "".join(char for char in TELEGRAM_BOT_TOKEN if ord(char) > 32)

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Xato: TELEGRAM_BOT_TOKEN .env faylida sozlanmagan!")
        print("Iltimos, .env faylini tahrirlang va haqiqiy bot tokenini kiriting.")
        return

    if not check_ffmpeg_available():
        logger.warning("FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        print("⚠️  FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        print("💡 FFmpeg ni o'rnatish uchun:")
        print("   Windows: https://ffmpeg.org/download.html dan yuklab oling")
        print("   MacOS: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishga tushirilmoqda...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n🔄 Bot o'chirilmoqda...")
        logger.info("Bot KeyboardInterrupt orqali o'chirildi")
        print("✅ Bot to'g'ri o'chirildi")
    except Exception as e:
        logger.error(f"Bot ishga tushirishda xatolik: {e}")
        print(f"❌ Bot ishga tushirishda xatolik: {e}")


if __name__ == '__main__':
    main()
