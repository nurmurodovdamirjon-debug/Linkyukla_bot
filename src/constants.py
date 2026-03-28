# -*- coding: utf-8 -*-
"""
Loyiha bo'ylab ishlatiladigan o'zgarmas qiymatlar (Constants)
"""

from telegram import InlineKeyboardButton

# =============================================================================
# VIDEO CHEKLOVLARI
# =============================================================================
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB (Telegram limiti)
MAX_VIDEO_DURATION = 6000  # 100 daqiqa (soniyalarda)
DEFAULT_VIDEO_DURATION = 6000  # Default agar .env da sozlanmagan bo'lsa

# =============================================================================
# TELEGRAM CHEKLOVLARI
# =============================================================================
CAPTION_MAX_LENGTH = 1024  # Caption uchun belgilar soni
MESSAGE_MAX_LENGTH = 4096  # Xabar uchun belgilar soni

# =============================================================================
# FAYL NOMLARI VA KATALOGLAR
# =============================================================================
DOWNLOAD_DIR = "downloads"
DEFAULT_LOG_LEVEL = "INFO"
LOG_FILENAME = "bot.log"

# =============================================================================
# PLATFORMA MA'LUMOTLARI
# =============================================================================
PLATFORM_EMOJIS = {
    'youtube': '🔴',
    'instagram': '📸',
    'tiktok': '🎵',
    'twitter': '🐦',
    'vimeo': '🔷',
    'facebook': '📘',
    'unknown': '❓'
}

PLATFORM_NAMES = {
    'youtube': 'YouTube',
    'instagram': 'Instagram',
    'tiktok': 'TikTok',
    'twitter': 'Twitter',
    'vimeo': 'Vimeo',
    'facebook': 'Facebook',
    'unknown': 'Boshqa'
}

PLATFORM_BUTTON_TEXTS = {
    'youtube': 'YouTube Videosi',
    'instagram': 'Instagram Videosi',
    'tiktok': 'TikTok Videosi',
    'twitter': 'Twitter Videosi',
    'vimeo': 'Vimeo Videosi',
    'facebook': 'Facebook Videosi',
    'unknown': 'Video'
}

PLATFORM_EXAMPLE_URLS = {
    'youtube': 'https://www.youtube.com/watch?v=example',
    'instagram': 'https://www.instagram.com/p/example/',
    'tiktok': 'https://www.tiktok.com/@user/video/example',
    'twitter': 'https://twitter.com/user/status/example',
    'vimeo': 'https://vimeo.com/example',
    'facebook': 'https://www.facebook.com/user/videos/example'
}

# =============================================================================
# MAIN MENU KEYBOARD (Duplicate code oldini olish uchun)
# =============================================================================
MAIN_MENU_KEYBOARD = [
    [InlineKeyboardButton(f"{PLATFORM_EMOJIS['youtube']} YouTube", callback_data="platform_youtube")],
    [InlineKeyboardButton(f"{PLATFORM_EMOJIS['instagram']} Instagram", callback_data="platform_instagram")],
    [InlineKeyboardButton(f"{PLATFORM_EMOJIS['tiktok']} TikTok", callback_data="platform_tiktok")],
    [InlineKeyboardButton(f"{PLATFORM_EMOJIS['twitter']} Twitter", callback_data="platform_twitter")],
    [InlineKeyboardButton(f"{PLATFORM_EMOJIS['vimeo']} Vimeo", callback_data="platform_vimeo")],
    [InlineKeyboardButton(f"{PLATFORM_EMOJIS['facebook']} Facebook", callback_data="platform_facebook")]
]

# =============================================================================
# TARJIMA SOZLAMALARI
# =============================================================================
TRANSLATION_TARGET_LANG = 'uz'
TRANSLATION_TEXT_LIMIT = 5000
DESCRIPTION_PREVIEW_LENGTH = 300
CAPTION_PREVIEW_LENGTH = 200

# =============================================================================
# HTTP VA TARMOQ SOZLAMALARI
# =============================================================================
HTTP_TIMEOUT = 30
REQUEST_RETRIES = 3
SOCKET_TIMEOUT = 30
FRAGMENT_RETRIES = 3

# =============================================================================
# HEALTH CHECK
# =============================================================================
HEALTH_CHECK_PORT = 8000
HEALTH_CHECK_HOST = '0.0.0.0'

# =============================================================================
# YT-DLP SOZLAMALARI
# =============================================================================
YT_DLP_SLEEP_INTERVAL = 1
YT_DLP_MAX_SLEEP_INTERVAL = 5
YT_DLP_RETRIES = 3

# =============================================================================
# WELCOME MESSAGE (Duplicate code oldini olish uchun)
# =============================================================================
WELCOME_MESSAGE = """👋 Salom {name}!

Men turli platformalardan videolarni yuklab olishga yordam beradigan ilg'or video botman.

📥 Menga video URL manzilini yuboring va men uni siz uchun yuklab olaman.
✅ Qo'llab-quvvatlanadigan platformalar:
• 🟥 YouTube
• 📸 Instagram
• 🎵 TikTok
• 🐦 Twitter/X
• 🔷 Vimeo
• 📘 Facebook

⚠️ Eslatma: Telegram cheklovlari tufayli 50MB dan katta videolar maxsus usullar bilan yuboriladi.

👨‍💻 Muallif: N.Damir - Senior Dasturchi"""

# =============================================================================
# HELP MESSAGE
# =============================================================================
HELP_MESSAGE = """🤖 Video Yuklab Olish Boti Yordami

Men sizga turli platformalardan videolarni yuklab olishga yordam beraman.

📥 Foydalanish bo'yicha qo'llanma:
1. Menga yuklab olmoqchi bo'lgan videoning URL manzilini yuboring.
2. Men uni qayta ishlab, videoni qaytaraman.

📋 Qo'llab-quvvatlanadigan platformalar:
• 🟥 YouTube
• 📸 Instagram
• 🎵 TikTok
• 🐦 Twitter/X
• 🔷 Vimeo
• 📘 Facebook

⚠️ Cheklovlar:
• 100 daqiqadan ortiq videolarni yuklab olib bo'lmaydi.
• 50MB dan katta videolar maxsus usullar bilan yuboriladi.
• Ba'zi saytlar yuklab olishni cheklaydi.

⌨️ Buyruqlar:
/start - Botni ishga tushirish
/help - Ushbu yordam xabarini ko'rsatish
/about - Bot haqida ma'lumot ko'rsatish"""

# =============================================================================
# ABOUT MESSAGE
# =============================================================================
ABOUT_MESSAGE = """📹 Video Yuklab Olish Boti

Ushbu bot sizga turli platformalardan videolarni bevosita Telegramga yuklab olish imkonini beradi.

🛠 Foydalanilgan texnologiyalar:
• 🐍 python-telegram-bot
• 📥 yt-dlp
• 🌐 deep-translator (tarjima uchun)

👨‍💻 Dasturchi:
N.Damir - Senior Dasturchi

🔒 Maxfiylik:
Hech qanday video yoki shaxsiy ma'lumot serverlarimizda saqlanmaydi.
Barcha qayta ishlash vaqtinchalik amalga oshiriladi va fayllar yuborilgandan keyin o'chirib tashlanadi."""

# =============================================================================
# YOUTUBE XATO XABARI
# =============================================================================
YOUTUBE_BOT_ERROR_MESSAGE = """❌ YouTube bot tekshiruvi aniqlandi!

💡 Yechimlar:
1. Boshqa video manbasi tanlang (Instagram, TikTok, Vimeo, Twitter)
2. Video manzilini tekshirib ko'ring
3. Mahalliy kompyuteringizda botni ishga tushiring

📢 YouTube hozirda avtomatik yuklab olishni faol cheklamoqda. Bu xavfsizlik chorasi bo'lib, botlarning tizimdan foydalanishini oldini oladi.

🔧 YouTube uchun tavsiyalar:
• cookies.txt faylini qo'shing (YouTube hisobingizdan)
• Proxy serverdan foydalaning
• Video manzilini tekshiring
• Boshqa video manbasidan foydalaning

🔄 Tavsiya: Boshqa platformalardan video yuklab oling. Instagram, TikTok va Vimeo saytlari YouTube qanday cheklovlarsiz ishlaydi."""

# =============================================================================
# ALTERNATIVE FORMATS (YouTube uchun)
# =============================================================================
YOUTUBE_ALTERNATIVE_FORMATS = [
    {'format': 'worst'},
    {'format': 'best[height<=480]'},
    {'format': 'best[height<=360]'},
    {'format': 'mp4[height<=480]'},
    {'format': 'worst[height>=240]'},
]
