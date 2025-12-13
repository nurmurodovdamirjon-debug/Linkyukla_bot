#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Video Yuklab Olish Boti
Ushbu bot foydalanuvchilarga URL manzilini yuborish orqali turli platformalardan videolarni yuklab olish imkonini beradi.
"""

import logging
import os
import hashlib
import time
import asyncio
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

# Emoji kutubxonasini import qilish
try:
    import emoji
    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False
    print("Emoji kutubxonasi mavjud emas.")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

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

# Platforma aniqlash funksiyasi
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

# Platforma uchun stiker va tugma matni
def get_platform_sticker(platform):
    """Platformaga mos stiker va tugma matnini qaytarish."""
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

def get_youtube_alternatives():
    """YouTube uchun alternativ yuklab olish metodlari."""
    return [
        # 1. Oddiy formatlar
        lambda opts: dict(opts, format='worst'),
        # 2. Faqat video (bez audio)
        lambda opts: dict(opts, format='best[height<=480]'),
        # 3. Faqat video (past sifat)
        lambda opts: dict(opts, format='best[height<=360]'),
        # 4. Mobil formatlar
        lambda opts: dict(opts, format='mp4[height<=480]'),
    ]

async def download_with_youtube_retry(url, ydl_opts, progress_message):
    """YouTube uchun qayta urinish bilan yuklab olish."""
    import yt_dlp
    import asyncio
    import random
    
    # YouTube alternativ metodlari
    youtube_alternatives = get_youtube_alternatives()
    
    # Videoni yuklab olish
    download_success = False
    max_attempts = 3
    attempt = 0
    delay_strategies = [1, 3, 5]  # Turli darajadagi kechikishlar
    alt_index = 0  # Alternativ metodlar indeksi
    
    while attempt < max_attempts and not download_success:
        try:
            # Har bir urinishda tasodifiy kechikish
            if attempt > 0:
                delay = random.choice(delay_strategies)
                logger.info(f"YouTube uchun {delay} soniya kutish (urinish: {attempt + 1})")
                await asyncio.sleep(delay)
            
            # Videoni yuklab olish
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Video yuklab olishga harakat qilinmoqda: {url}")
                info_dict = ydl.extract_info(url, download=True)
                video_filename = ydl.prepare_filename(info_dict)
                logger.info(f"Video muvaffaqiyatli yuklab olindi: {video_filename}")
            download_success = True
            return info_dict, video_filename
        except yt_dlp.DownloadError as e:
            attempt += 1
            error_msg = str(e).lower()
            logger.error(f"Yuklab olish xatosi (urinish {attempt}): {error_msg}")
            
            # YouTube bot yoki cheklov xatolari
            if ('bot' in error_msg or '429' in error_msg or "confirm you're not a bot" in error_msg or 'sign in' in error_msg) and ('youtube.com' in url or 'youtu.be' in url):
                # Agar bu YouTube bot xatosi bo'lsa, alternativ metodlarni sinab ko'rish
                if alt_index < len(youtube_alternatives):
                    ydl_opts = youtube_alternatives[alt_index](ydl_opts)
                    alt_index += 1
                    attempt = 0  # Urinishlar sonini qayta boshlash
                    await progress_message.edit_text(f"🎵 YouTube cheklovi uchun alternativ usul sinab ko'rilmoqda...")
                    logger.info(f"YouTube uchun alternativ format sinab ko'rilmoqda (index: {alt_index})")
                else:
                    raise e  # Barcha alternativ metodlar sinab ko'rilgandan keyin xatoni qaytarish
            elif attempt >= max_attempts:
                raise e  # Oxirgi urinish ham muvaffaqiyatsiz bo'lsa, xatoni qaytarish
            else:
                # Kutish va qayta urinish
                logger.info(f"Qayta urinish uchun kutish: {attempt + 1}/{max_attempts}")
    
    # Agar yuklab olinmasa, xatoni qaytarish
    raise Exception("YouTube videoni yuklab olishda barcha urinishlar muvaffaqiyatsiz tugadi")
    """FFmpeg mavjudligini tekshirish."""
    try:
        import shutil
        return shutil.which('ffmpeg') is not None
    except:
        return False

def sanitize_filename(filename):
    """Fayl nomini tozalash - maxsus belgilarni olib tashlash."""
    import re
    import os as os_module
    
    # Fayl nomidan maxsus belgilarni olib tashlash
    clean_name = re.sub(r'[<>:"/\|?*\x00-\x1f]', '_', filename)
    # Ko'p bo'shliqlarni bittaga qisqartirish
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    # Fayl nomi juda uzun bo'lsa, qisqartirish
    if len(clean_name) > 150:
        clean_name = clean_name[:150]
    
    return clean_name

def extract_audio_from_video(video_path):
    """Videodan audio ajratib olish."""
    if not check_ffmpeg_available():
        return None
    
    try:
        import os
        # Audio fayl nomini yaratish
        audio_path = video_path.rsplit('.', 1)[0] + '_audio.mp3'
        
        # FFmpeg orqali audio ajratish
        import subprocess
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
        # Matn uzunligini tekshirish (Google Translate limiti)
        if len(text) > 5000:
            text = text[:5000]  # Matnni qisqartirish
            
        # Matnni tarjima qilish
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        logger.error(f"Tarjima xatosi: {str(e)}")
        return text  # Xatolik yuz bersa, original matnni qaytarish

async def send_instagram_content_separately(update, video_filename, info_dict, platform_sticker, platform_button_text):
    """Instagram video va audioni alohida yuborish."""
    try:
        video_title = info_dict.get('title', 'Instagram video')
        
        # Video faylini yuborish
        with open(video_filename, 'rb') as video_file:
            caption_text = f"{platform_sticker} {platform_button_text} (Video): {video_title}"
            
            # Instagram caption mavjud bo'lsa
            if info_dict.get('description'):
                instagram_caption = info_dict.get('description', '')
                if len(instagram_caption) > 200:
                    caption_text += f"\n\n📢 Caption:\n{instagram_caption[:200]}..."
                else:
                    caption_text += f"\n\n📢 Caption:\n{instagram_caption}"
                
                # Agar tarjima mavjud bo'lsa
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
        
        # Audio ajratish (agar FFmpeg mavjud bo'lsa)
        if check_ffmpeg_available():
            await update.message.reply_text("🎵 Audioni ajratish jarayoni boshlanmoqda...")
            
            audio_path = extract_audio_from_video(video_filename)
            if audio_path and os.path.exists(audio_path):
                # Audio fayl hajmini tekshirish
                audio_size = os.path.getsize(audio_path)
                max_size = int(os.getenv("MAX_VIDEO_SIZE", "52428800"))  # 50MB
                
                if audio_size <= max_size:
                    with open(audio_path, 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            title=f"{video_title} (Audio)",
                            caption=f"{platform_sticker} {platform_button_text} (Audio): {video_title}"
                        )
                    # Audio faylni o'chirish
                    os.remove(audio_path)
                else:
                    await update.message.reply_text(
                        f"❌ Audio fayl juda katta ({audio_size / (1024*1024):.1f}MB). "
                        f"Telegram faqat {max_size / (1024*1024):.0f}MB gacha fayllarni yuborishga ruxsat beradi."
                    )
            else:
                await update.message.reply_text("❌ Audioni ajratishda xatolik yuz berdi.")
        else:
            # FFmpeg o'rnatilmaganligi haqida xabar
            ffmpeg_message = (
                "ℹ️ Audio ajratish uchun FFmpeg kerak.\n\n"
                "FFmpeg ni o'rnatish uchun:\n"
                "Windows: https://ffmpeg.org/download.html dan yuklab oling\n"
                "MacOS: brew install ffmpeg\n"
                "Linux: sudo apt install ffmpeg"
            )
            await update.message.reply_text(ffmpeg_message)
            
    except Exception as e:
        logger.error(f"Instagram contentni alohida yuborishda xatolik: {str(e)}")
        raise
    """Matnni berilgan tilga tarjima qilish."""
    if not TRANSLATION_AVAILABLE or not text:
        return text
    
    try:
        # Matn uzunligini tekshirish (Google Translate limiti)
        if len(text) > 5000:
            text = text[:5000]  # Matnni qisqartirish
            
        # Matnni tarjima qilish
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        logger.error(f"Tarjima xatosi: {str(e)}")
        return text  # Xatolik yuz bersa, original matnni qaytarish

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi /start buyrug'ini berganida xabar yuborish."""
    user = update.effective_user
    if user:
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
        if update.message:
            # Platform selection buttons
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
    else:
        if update.message:
            await update.message.reply_text("Foydalanuvchi ma'lumotlarini olish imkonsiz.")

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
        "• 🌐 deep-translator (tarjima uchun)\n"
        "• 😊 emoji (stikerlar uchun)\n\n"
        "👨‍💻 Dasturchi:\n"
        "N.Damir - Senior Dasturchi\n\n"
        "🔒 Maxfiylik:\n"
        "Hech qanday video yoki shaxsiy ma'lumot serverlarimizda saqlanmaydi.\n"
        "Barcha qayta ishlash vaqtinchalik amalga oshiriladi va fayllar yuborilgandan keyin o'chirib tashlanadi."
    )
    if update.message:
        await update.message.reply_text(about_text)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """URL manzildan video yuklab olish va foydalanuvchiga yuborish."""
    if not update.message or not update.message.text:
        return
        
    url = update.message.text
    user = update.effective_user
    
    if not user:
        await update.message.reply_text("Foydalanuvchi ma'lumotlarini olish imkonsiz.")
        return
        
    logger.info(f"Foydalanuvchi {user.first_name} ({user.id}) quyidagi uchun yuklab olishni so'radi: {url}")
    
    # Platformani aniqlash
    platform = detect_platform(url)
    platform_sticker = get_platform_sticker(platform)
    platform_button_text = get_platform_button_text(platform)
    
    # Boshlang'ich xabar yuborish
    progress_message = await update.message.reply_text(f"{platform_sticker} So'rovingiz qayta ishlanmoqda...")
    
    try:
        # yt-dlp opsiyalarini sozlash
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOADS_DIR, f'{user.id}_%(title)s.%(ext)s'),
            'restrictfilenames': True,  # Fayl nomlarini cheklash
            'format': 'best[height<=720]/best[height<=480]/best',
            'sleep_interval': 1,
            'max_sleep_interval': 5,
        }
        
        # YouTube uchun maxsus sozlamalar
        if 'youtube.com' in url or 'youtu.be' in url:
            # YouTube helper dan opsiyalarni olish
            ydl_opts = youtube_helper.get_youtube_options(url)
            
            # Cookies faylini qo'shish (agar mavjud bo'lsa)
            ydl_opts = youtube_helper.add_cookies_to_options(ydl_opts)
            
            # YouTube uchun qo'shimcha opsiyalar
            ydl_opts['youtube_include_dash_manifest'] = False
            ydl_opts['youtube_include_hls_manifest'] = False
            
            # YouTube formatlarini optimallashtirish
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            
            # YouTube bot yoki cheklov xatolari uchun qayta urinish strategiyalari
            youtube_alternatives = youtube_helper.get_alternative_formats()
        else:
            # Boshqa platformalar uchun oddiy sozlamalar
            ydl_opts.update({
                'format': 'best[height<=720]/best[height<=480]/best',
                'sleep_interval': 1,
                'max_sleep_interval': 5,
            })
            
            # Proxy sozlamalari (agar mavjud bo'lsa)
            proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
            if proxy_url:
                ydl_opts['proxy'] = proxy_url
                
            # Cookies faylini sozlash (Railway uchun maxsus)
            cookies_content = os.getenv('COOKIES_CONTENT')
            if cookies_content:
                # Railway uchun cookies faylini yaratish
                cookies_path = os.path.join(DOWNLOADS_DIR, 'cookies.txt')
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    f.write(cookies_content)
                ydl_opts['cookies'] = cookies_path
            else:
                # Lokal foydalanish uchun mavjud cookies.txt fayli
                if os.path.exists('cookies.txt'):
                    ydl_opts['cookies'] = 'cookies.txt'
        
        # Proxy sozlamalari (agar mavjud bo'lsa)
        proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
        if proxy_url:
            ydl_opts['proxy'] = proxy_url
            
        # Cookies faylini sozlash (Railway uchun maxsus)
        cookies_content = os.getenv('COOKIES_CONTENT')
        if cookies_content:
            # Railway uchun cookies faylini yaratish
            cookies_path = os.path.join(DOWNLOADS_DIR, 'cookies.txt')
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write(cookies_content)
            ydl_opts['cookies'] = cookies_path
        else:
            # Lokal foydalanish uchun mavjud cookies.txt fayli
            if os.path.exists('cookies.txt'):
                ydl_opts['cookies'] = 'cookies.txt'
        
        # FFmpeg mavjudligini tekshirish va opsiyalar qo'shish
        import shutil
        if shutil.which('ffmpeg'):
            ydl_opts['format'] = 'best[height<=720]+bestaudio/best[height<=480]/best'
        else:
            logger.warning("FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        
        # Instagram uchun qo'shimcha format sozlamalari
        if 'instagram.com' in url or 'instagr.am' in url:
            ydl_opts['format'] = 'best[height<=720]/best[height<=480]/best'
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = ['en', 'ru', 'uz', 'all']
            # Instagram uchun maxsus sozlamalar
            ydl_opts['extractor_args'] = {
                'instagram': {
                    'api': 'web',
                    'include_ads': False,
                    'include_paid_promotion': False,
                }
            }
        
        # Jarayonni yangilash
        await progress_message.edit_text(f"{platform_sticker} Video tahlil qilinmoqda...")
        
        # Avval video ma'lumotlarini olish
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            if info_dict is None:
                await progress_message.edit_text(
                    "Kechirasiz, men bu videoni tahlil qila olmadim.\n"
                    "Iltimos, URL manzil to'g'ri ekanligini tekshiring."
                )
                return
                
            # Debug uchun ma'lumotlarni log qilish
            logger.info(f"Video info keys: {list(info_dict.keys())}")
            if 'instagram.com' in url:
                logger.info(f"Instagram video info - description: {info_dict.get('description', 'No description')}")
                logger.info(f"Instagram video info - subtitles: {info_dict.get('subtitles', 'No subtitles')}")
                logger.info(f"Instagram video info - automatic_captions: {info_dict.get('automatic_captions', 'No auto captions')}")
                
            video_title = info_dict.get('title', 'video')
            video_duration = info_dict.get('duration', 0)
            video_description = info_dict.get('description', '')
        
        # Agar video juda uzun bo'lsa (100 daqiqadan ortiq)
        max_duration_env = os.getenv("MAX_VIDEO_DURATION", "6000")
        max_duration = int(max_duration_env)
        if max_duration == 600:
            max_duration = 6000
            logger.info("MAX_VIDEO_DURATION 600 dan 6000 ga o'zgartirildi")
        
        if video_duration > max_duration:
            await progress_message.edit_text(
                f"Kechirasiz, men {max_duration // 60} daqiqadan ortiq videolarni yuklab ololmayman.\n"
                f"Video davomiyligi: {video_duration // 60} daqiqa"
            )
            return
        
        # Jarayonni yangilash
        await progress_message.edit_text(f"{platform_sticker} Video yuklab olinmoqda...")
        
        # YouTube uchun maxsus yuklab olish
        if 'youtube.com' in url or 'youtu.be' in url:
            try:
                info_dict, video_filename = await youtube_helper.download_with_youtube_retry(url, ydl_opts, progress_message)
            except Exception as e:
                logger.error(f"YouTube yuklab olishda xatolik: {str(e)}")
                
                # YouTube bot xatolarini tekshirish
                error_msg = str(e).lower()
                if youtube_helper.is_youtube_bot_error(error_msg):
                    # YouTube bot xatolari uchun maxsus xabar
                    await progress_message.edit_text(youtube_helper.get_youtube_error_message())
                else:
                    await progress_message.edit_text(
                        f"Kechirasiz, men YouTube videosini yuklab ololmadim.\n"
                        f"Xato: {str(e)[:200]}..."
                    )
                return
        else:
            # Boshqa platformalar uchun oddiy yuklab olish
            try:
                # Videoni yuklab olish
                download_success = False
                max_attempts = 3 if 'youtube.com' in url or 'youtu.be' in url else 1
                attempt = 0
                
                # YouTube uchun alternativ metodlar
                youtube_alternatives = [
                    lambda opts: dict(opts, format='worst'),  # Eng past sifat
                    lambda opts: dict(opts, format='best[height<=480]'),  # 480p gacha
                    lambda opts: dict(opts, format='best[height<=360]'),  # 360p gacha
                ]
                
                # Kechikish strategiyalari
                delay_strategies = [1, 3, 5]  # Turli darajadagi kechikishlar
                
                alt_index = 0
                while attempt < max_attempts and not download_success:
                    try:
                        # Har bir urinishda tasodifiy kechikish
                        if attempt > 0:
                            import random
                            delay = random.choice(delay_strategies)
                            logger.info(f"Urinish uchun {delay} soniya kutish (urinish: {attempt + 1})")
                            await asyncio.sleep(delay)
                        
                        # Videoni yuklab olish
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            logger.info(f"Video yuklab olishga harakat qilinmoqda: {url}")
                            info_dict = ydl.extract_info(url, download=True)
                            video_filename = ydl.prepare_filename(info_dict)
                            logger.info(f"Video muvaffaqiyatli yuklab olindi: {video_filename}")
                            
                            # Fayl nomini tozalash (agar kerak bo'lsa)
                            import os as os_module
                            if os_module.path.exists(video_filename):
                                # Tozalangan fayl nomini yaratish
                                dir_name = os_module.path.dirname(video_filename)
                                base_name = os_module.path.basename(video_filename)
                                name, ext = os_module.path.splitext(base_name)
                                
                                # Fayl nomini tozalash
                                clean_name = sanitize_filename(name)
                                clean_filename = os_module.path.join(dir_name, f"{clean_name}{ext}")
                                
                                # Agar fayl nomi o'zgargan bo'lsa, faylni qayta nomlash
                                if clean_filename != video_filename:
                                    try:
                                        os_module.rename(video_filename, clean_filename)
                                        video_filename = clean_filename
                                        logger.info(f"Fayl nomi tozalandi: {video_filename}")
                                    except Exception as e:
                                        logger.error(f"Fayl nomini tozalashda xatolik: {str(e)}")
                                        # Xatolik yuz bersa, original fayl nomidan foydalanamiz
                        download_success = True
                    except yt_dlp.DownloadError as e:
                        attempt += 1
                        error_msg = str(e).lower()
                        logger.error(f"Yuklab olish xatosi (urinish {attempt}): {error_msg}")
                        
                        # YouTube bot yoki cheklov xatolari
                        if ('bot' in error_msg or '429' in error_msg or 'confirm you\'re not a bot' in error_msg or 'sign in' in error_msg) and ('youtube.com' in url or 'youtu.be' in url):
                            # Agar bu YouTube bot xatosi bo'lsa, alternativ metodlarni sinab ko'rish
                            if alt_index < len(youtube_alternatives):
                                ydl_opts = youtube_alternatives[alt_index](ydl_opts)
                                alt_index += 1
                                attempt = 0  # Urinishlar sonini qayta boshlash
                                await progress_message.edit_text(f"{platform_sticker} YouTube cheklovi uchun alternativ usul sinab ko'rilmoqda...")
                                logger.info(f"YouTube uchun alternativ format sinab ko'rilmoqda (index: {alt_index})")
                            else:
                                # YouTube uchun maxsus xatolik
                                await progress_message.edit_text(
                                    "❌ YouTube bot tekshiruvi aniqlandi!\n\n"
                                    "💡 Yechimlar:\n"
                                    "1. Boshqa video manbasi tanlang (Instagram, TikTok, Vimeo, Twitter)\n"
                                    "2. Video manzilini tekshirib ko'ring\n"
                                    "3. Mahalliy kompyuteringizda botni ishga tushiring\n\n"
                                    "📢 YouTube hozirda avtomatik yuklab olishni faol cheklamoqda. "
                                    "Bu xavfsizlik chorasi bo'lib, botlarning tizimdan foydalanishini oldini oladi."
                                )
                                return
                        elif attempt >= max_attempts:
                            raise e  # Oxirgi urinish ham muvaffaqiyatsiz bo'lsa, xatoni qaytarish
                        else:
                            # Kutish va qayta urinish
                            logger.info(f"Qayta urinish uchun kutish: {attempt + 1}/{max_attempts}")
            except Exception as e:
                logger.error(f"Yuklab olishda umumiy xatolik: {str(e)}")
                
                # YouTube bot xatolarini tekshirish
                error_msg = str(e).lower()
                if youtube_helper.is_youtube_bot_error(error_msg) and ('youtube.com' in url or 'youtu.be' in url):
                    # YouTube bot xatolari uchun maxsus xabar
                    await progress_message.edit_text(youtube_helper.get_youtube_error_message())
                else:
                    await progress_message.edit_text(
                        f"Kechirasiz, men videoni yuklab ololmadim.\n"
                        f"Xato: {str(e)[:200]}..."
                    )
                return
        
        # Fayl mavjudligini tekshirish
        if not os.path.exists(video_filename):
            await progress_message.edit_text(
                "Kechirasiz, men videoni yuklab ololmadim.\n"
                "Fayl yaratilmadi."
            )
            return
        
        # Fayl mavjudligini tekshirish
        if not os.path.exists(video_filename):
            await progress_message.edit_text(
                "Kechirasiz, men videoni yuklab ololmadim.\n"
                "Fayl yaratilmadi."
            )
            return
        
        # Fayl hajmini tekshirish
        file_size = os.path.getsize(video_filename)
        max_size = int(os.getenv("MAX_VIDEO_SIZE", "52428800"))  # 50MB baytlarda
        
        if file_size > max_size:
            await progress_message.edit_text(
                f"📹 Video fayl juda katta ({file_size / (1024*1024):.1f}MB).\n"
                f"Telegram faqat {max_size / (1024*1024):.0f}MB gacha fayllarni yuborishga ruxsat beradi.\n\n"
                f"Quyidagi variantlardan birini tanlang:"
            )
            return
        
        await progress_message.edit_text(f"{platform_sticker} Video Telegramga yuklanmoqda...")
        
        # Foydalanuvchiga video yuborish
        with open(video_filename, 'rb') as video_file:
            caption_text = f"{platform_sticker} {platform_button_text}: {video_title}"
            
            # Subtitle mavjudligini tekshirish va tarjima qilish
            subtitle_info = ""
            
            # Instagram uchun maxsus caption tekshiruvi
            if 'instagram.com' in url or 'instagr.am' in url:
                # Instagram captionlarini tekshirish
                if info_dict.get('description'):
                    instagram_caption = info_dict.get('description', '')
                    if instagram_caption and len(instagram_caption) > 0:
                        subtitle_info += "\n\n📢 Instagram Caption:\n"
                        # Caption uzunligini cheklash
                        if len(instagram_caption) > 300:
                            subtitle_info += instagram_caption[:300] + "..."
                        else:
                            subtitle_info += instagram_caption
                        
                        # Agar tarjima mavjud bo'lsa
                        if TRANSLATION_AVAILABLE:
                            try:
                                translated_caption = translate_text(instagram_caption, 'uz')
                                if translated_caption and translated_caption != instagram_caption:
                                    subtitle_info += f"\n\n🔄 Tarjima:\n{translated_caption[:300]}{'...' if len(translated_caption) > 300 else ''}"
                            except Exception as e:
                                logger.error(f"Tarjima xatosi: {str(e)}")
            
            # Boshqa platformalar uchun subtitle tekshiruvi
            elif info_dict.get('subtitles') or info_dict.get('automatic_captions'):
                subtitle_info += "\n\n📢 Subtitles:\n"
                subtitles = info_dict.get('subtitles', {})
                auto_captions = info_dict.get('automatic_captions', {})
                
                # Avtomatik subtitlelar mavjudligini tekshirish
                if auto_captions:
                    subtitle_info += "🤖 Avtomatik titrlar mavjud\n"
                elif subtitles:
                    subtitle_info += "📝 Qo'lda titrlar mavjud\n"
                
                # Agar tarjima mavjud bo'lsa
                if TRANSLATION_AVAILABLE:
                    try:
                        description = info_dict.get('description', '')
                        if description and len(description) > 0:
                            # Izoh uchun tarjima
                            translated_desc = translate_text(description, 'uz')
                            if translated_desc and translated_desc != description:
                                subtitle_info += f"\n🔄 Tarjima:\n{translated_desc[:200]}{'...' if len(translated_desc) > 200 else ''}"
                    except Exception as e:
                        logger.error(f"Tarjima xatosi: {str(e)}")
            
            # Umumiy description mavjud bo'lsa (boshqa platformalar uchun)
            elif info_dict.get('description'):
                description = info_dict.get('description', '')
                if description and len(description) > 0:
                    subtitle_info += "\n\n📢 Video Description:\n"
                    # Description uzunligini cheklash
                    if len(description) > 300:
                        subtitle_info += description[:300] + "..."
                    else:
                        subtitle_info += description
                    
                    # Agar tarjima mavjud bo'lsa
                    if TRANSLATION_AVAILABLE:
                        try:
                            translated_desc = translate_text(description, 'uz')
                            if translated_desc and translated_desc != description:
                                subtitle_info += f"\n\n🔄 Tarjima:\n{translated_desc[:300]}{'...' if len(translated_desc) > 300 else ''}"
                        except Exception as e:
                            logger.error(f"Tarjima xatosi: {str(e)}")

            # Subtitle ma'lumotini captionga qo'shish
            if subtitle_info:
                # Caption uzunligini tekshirish (Telegram limiti 1024 belgi)
                if len(caption_text + subtitle_info) <= 1024:
                    caption_text += subtitle_info
                else:
                    # Agar caption juda uzun bo'lsa, qisqartirish
                    available_length = 1024 - len(caption_text) - 50  # 50 belgi rezerv
                    if available_length > 100:
                        caption_text += subtitle_info[:available_length] + "..."

            # Instagram uchun alohida video/audio yuborish variantini taklif qilish
            if 'instagram.com' in url or 'instagr.am' in url:
                # Oddiy tarzda video yuborish (caption bilan)
                await update.message.reply_video(
                    video=video_file,
                    caption=caption_text,
                    supports_streaming=True
                )
            else:
                # Boshqa platformalar uchun oddiy tarzda yuborish
                await update.message.reply_video(
                    video=video_file,
                    caption=caption_text,
                    supports_streaming=True
                )
        
        # Yuklab olingan faylni tozalash
        os.remove(video_filename)
        
        # Progress message'ni o'chirish
        try:
            await progress_message.delete()
        except:
            pass
        
    except yt_dlp.DownloadError as e:
        logger.error(f"Yuklab olish xatosi: {str(e)}")
        error_msg = str(e)
        if 'Unsupported URL' in error_msg:
            if 'mover.uz' in url:
                await progress_message.edit_text(
                    "Kechirasiz, men Mover.uz saytidan video yuklab olishni qo'llab-quvvatlamayman.\n"
                    "Mover.uz saytida video yuklab olish uchun ularning o'zlarining dasturidan foydalaning.\n\n"
                    "Men YouTube, Vimeo, Twitter, Instagram, TikTok va boshqa saytlarni qo'llab-quvvatlayman."
                )
            else:
                await progress_message.edit_text(
                    "Kechirasiz, men bu saytdan yuklab olishni qo'llab-quvvatlamayman.\n"
                    "Men YouTube, Vimeo, Twitter, Instagram, TikTok va minglab boshqa saytlarni qo'llab-quvvatlayman."
                )
        elif 'Sign in to confirm you\'re not a bot' in error_msg or 'bot' in error_msg.lower() or '429' in error_msg or 'unable to download webpage' in error_msg.lower():
            # Railway deployment uchun maxsus xabar
            railway_msg = ""
            if os.getenv('RAILWAY_ENVIRONMENT'):
                railway_msg = "\n\n\x1b[34m📍 Railway deployment aniqlandi. " \
                             "Ehtimol, Railway IP manzillari YouTube tomonidan cheklangan.\x1b[0m"
            
            # YouTube uchun maxsus tavsiyalar
            youtube_suggestions = ""
            if 'youtube.com' in url or 'youtu.be' in url:
                youtube_suggestions = "\n\n🔧 YouTube uchun tavsiyalar:\n" \
                                   "• cookies.txt faylini qo'shing (YouTube hisobingizdan)\n" \
                                   "• Proxy serverdan foydalaning\n" \
                                   "• Video manzilini tekshiring\n" \
                                   "• Boshqa video manbasidan foydalaning"
            
            await progress_message.edit_text(
                "❌ YouTube bot tekshiruvi aniqlandi!\n\n"
                "💡 Yechimlar:\n"
                "1. Boshqa video manbasi tanlang (Instagram, TikTok, Vimeo, Twitter)\n"
                "2. Video manzilini tekshirib ko'ring\n"
                "3. Mahalliy kompyuteringizda botni ishga tushiring\n\n"
                "📢 YouTube hozirda avtomatik yuklab olishni faol cheklamoqda. "
                "Bu xavfsizlik chorasi bo'lib, botlarning tizimdan foydalanishini oldini oladi." +
                railway_msg +
                youtube_suggestions +
                "\n\n🔄 Tavsiya: Boshqa platformalardan video yuklab oling. "
                "Instagram, TikTok va Vimeo saytlari YouTube qanday cheklovlarsiz ishlaydi."
            )
        else:
            await progress_message.edit_text(
                f"Kechirasiz, men videoni yuklab ololmadim.\n"
                f"Xato: {error_msg[:200]}..."
            )
    except Exception as e:
        logger.error(f"Kutilmagan xato: {str(e)}")
        await progress_message.edit_text(
            f"Kechirasiz, kutilmagan xato yuz berdi.\n"
            f"Xato: {str(e)}"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kiruvchi xabarlarni qayta ishlash."""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    user = update.effective_user
    
    user_name = user.first_name if user else "Noma'lum"
    logger.info(f"Foydalanuvchi {user_name} yubordi: {text}")
    
    # Agar xabar URL manzil bo'lsa
    if text.startswith('http'):
        await download_video(update, context)
    else:
        await update.message.reply_text(
            "Menga video yuklab olish uchun haqiqiy URL manzil yuboring.\n\n"
            "Masalan: https://www.youtube.com/watch?v=example"
        )

# Global o'zgaruvchilar
instagram_video_files = {}  # {user_id: {'video': video_filename, 'info': info_dict}}

# YouTube helper import qilish
from src.youtube_helper import youtube_helper

# Button handler import qilish
from src.buttons import button_handler

def check_ffmpeg_available():
    """FFmpeg mavjudligini tekshirish."""
    try:
        import shutil
        return shutil.which('ffmpeg') is not None
    except:
        return False

def check_and_create_cookies_file():
    """Cookies faylini tekshirish va agar kerak bo'lsa yaratish."""
    import os
    
    # Asosiy cookies fayllari
    cookies_files = [
        'cookies.txt',
        os.path.join(DOWNLOADS_DIR, 'cookies.txt'),
        os.path.join(os.getcwd(), 'cookies.txt')
    ]
    
    # Mavjud cookies faylini qidirish
    for cookies_file in cookies_files:
        if os.path.exists(cookies_file):
            logger.info(f"Cookies fayli topildi: {cookies_file}")
            return cookies_file
    
    # Agar cookies fayli mavjud bo'lmasa, Railway dan olingan cookies dan foydalanish
    cookies_content = os.getenv('COOKIES_CONTENT')
    if cookies_content:
        cookies_path = os.path.join(DOWNLOADS_DIR, 'cookies.txt')
        try:
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write(cookies_content)
            logger.info(f"Cookies fayli Railway dan yaratildi: {cookies_path}")
            return cookies_path
        except Exception as e:
            logger.error(f"Cookies faylini yaratishda xatolik: {str(e)}")
    
    # Agar cookies fayli mavjud bo'lmasa, foydalanuvchiga xabar berish
    logger.info("Cookies fayli topilmadi. YouTube uchun cookies fayli tavsiya etiladi.")
    return None

def main() -> None:
    """Botni ishga tushirish."""
    # .env fayldan bot tokenini olish
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Xato: TELEGRAM_BOT_TOKEN .env faylida sozlanmagan!")
        print("Iltimos, .env faylini tahrirlang va haqiqiy bot tokenini kiriting.")
        return
    
    # Cookies faylini tekshirish va yaratish
    check_and_create_cookies_file()
    
    # FFmpeg mavjudligini tekshirish
    if not check_ffmpeg_available():
        logger.warning("FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        print("⚠️  FFmpeg topilmadi. Yuklab olingan format eng yaxshi bo'lmasligi mumkin.")
        print("💡 FFmpeg ni o'rnatish uchun:")
        print("   Windows: https://ffmpeg.org/download.html dan yuklab oling")
        print("   MacOS: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")
    
    # Application yaratish va bot tokeningizni o'tkazish.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Foydalanuvchi Ctrl-C tugmachasini bosmaguncha botni ishga tushirish
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