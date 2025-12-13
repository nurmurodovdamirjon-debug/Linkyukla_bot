#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Helper - YouTube uchun maxsus algoritmlar va yechimlar
Ushbu fayl YouTube bot tekshiruvini chetlab o'tish uchun maxsus algoritmlarni o'z ichiga oladi.
"""

import logging
import os
import random
import time
import asyncio
from typing import Dict, Any, Optional, Tuple

# Logger yaratish
logger = logging.getLogger(__name__)

class YouTubeHelper:
    """YouTube uchun maxsus yordamchi klass."""
    
    def __init__(self):
        """YouTubeHelper obyektini yaratish."""
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        ]
        
        self.referers = [
            'https://www.google.com/',
            'https://www.youtube.com/',
            'https://www.google.ru/',
            'https://www.yandex.ru/',
            'https://duckduckgo.com/',
        ]
        
        self.accept_languages = [
            'en-US,en;q=0.9',
            'ru-RU,ru;q=0.9',
            'uz-UZ,uz;q=0.9',
            'tr-TR,tr;q=0.9',
            'de-DE,de;q=0.9',
            'fr-FR,fr;q=0.9',
        ]
        
        self.delays = [1, 2, 3, 5, 7, 10]  # Turli darajadagi kechikishlar
        
    def get_random_user_agent(self) -> str:
        """Tasodifiy user agent qaytarish."""
        return random.choice(self.user_agents)
    
    def get_random_referer(self) -> str:
        """Tasodifiy referer qaytarish."""
        return random.choice(self.referers)
    
    def get_random_accept_language(self) -> str:
        """Tasodifiy accept language qaytarish."""
        return random.choice(self.accept_languages)
    
    def get_random_delay(self) -> int:
        """Tasodifiy kechikish qaytarish."""
        return random.choice(self.delays)
    
    def get_youtube_headers(self) -> Dict[str, str]:
        """YouTube uchun headerlar qaytarish."""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': self.get_random_accept_language(),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': self.get_random_referer(),
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
        }
    
    def get_youtube_options(self, url: str) -> Dict[str, Any]:
        """YouTube uchun yt-dlp opsiyalarini qaytarish."""
        options = {
            'format': 'best[height<=720]/best[height<=480]/best',
            'merge_output_format': 'mp4',
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
            'http_headers': self.get_youtube_headers(),
            'nocheckcertificate': True,
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],  # Murakkab formatlarni o'tkazib yuborish
                    'player_skip': ['configs', 'webpage'],  # Player konfiguratsiyasini o'tkazib yuborish
                }
            },
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
        }
        
        # YouTube uchun maxsus opsiyalar
        if 'youtube.com' in url or 'youtu.be' in url:
            options['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            
        return options
    
    def get_alternative_formats(self) -> list:
        """YouTube uchun alternativ formatlar."""
        return [
            # 1. Oddiy formatlar
            lambda opts: dict(opts, format='worst'),
            # 2. Faqat video (bez audio)
            lambda opts: dict(opts, format='best[height<=480]'),
            # 3. Faqat video (past sifat)
            lambda opts: dict(opts, format='best[height<=360]'),
            # 4. Mobil formatlar
            lambda opts: dict(opts, format='mp4[height<=480]'),
            # 5. Eng oddiy format
            lambda opts: dict(opts, format='worst[height>=240]'),
        ]
    
    def add_cookies_to_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """YouTube cookies faylini opsiyalarga qo'shish."""
        # Cookies faylini tekshirish
        cookies_content = os.getenv('COOKIES_CONTENT')
        if cookies_content:
            # Railway uchun cookies faylini yaratish
            import tempfile
            import os as os_module
            
            # Vaqtinchalik fayl yaratish
            temp_dir = tempfile.gettempdir()
            cookies_path = os_module.path.join(temp_dir, 'youtube_cookies.txt')
            
            try:
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    f.write(cookies_content)
                options['cookiefile'] = cookies_path
                logger.info(f"YouTube cookies fayli yaratildi: {cookies_path}")
            except Exception as e:
                logger.error(f"YouTube cookies faylini yaratishda xatolik: {str(e)}")
        else:
            # Lokal foydalanish uchun mavjud cookies.txt fayli
            if os.path.exists('cookies.txt'):
                options['cookiefile'] = 'cookies.txt'
                logger.info("Mavjud cookies.txt fayli qo'shildi")
            elif os.path.exists(os.path.join('downloads', 'cookies.txt')):
                options['cookiefile'] = os.path.join('downloads', 'cookies.txt')
                logger.info("Mavjud downloads/cookies.txt fayli qo'shildi")
        
        return options
    
    async def wait_with_jitter(self, attempt: int):
        """Tasodifiy kechikish bilan kutish."""
        if attempt > 0:
            delay = self.get_random_delay() * attempt
            logger.info(f"YouTube uchun {delay} soniya kutish (urinish: {attempt + 1})")
            await asyncio.sleep(delay)
    
    def is_youtube_bot_error(self, error_msg: str) -> bool:
        """YouTube bot xatosini aniqlash."""
        error_msg_lower = error_msg.lower()
        youtube_indicators = [
            'bot',
            '429',
            'confirm you\'re not a bot',
            'sign in',
            'unable to download webpage',
            'rate limit',
            'too many requests',
            'blocked',
            'restricted',
            'forbidden'
        ]
        
        return any(indicator in error_msg_lower for indicator in youtube_indicators)
    
    def get_youtube_error_message(self) -> str:
        """YouTube bot xatolari uchun maxsus xabar."""
        railway_msg = ""
        if os.getenv('RAILWAY_ENVIRONMENT'):
            railway_msg = "\n\n📍 Railway deployment aniqlandi. " \
                         "Ehtimol, Railway IP manzillari YouTube tomonidan cheklangan."
        
        youtube_solutions = "\n\n🔧 YouTube uchun tavsiyalar:\n" \
                          "• cookies.txt faylini qo'shing (YouTube hisobingizdan)\n" \
                          "• Proxy serverdan foydalaning\n" \
                          "• Video manzilini tekshiring\n" \
                          "• Boshqa video manbasidan foydalaning"
        
        return (
            "❌ YouTube bot tekshiruvi aniqlandi!\n\n"
            "💡 Yechimlar:\n"
            "1. Boshqa video manbasi tanlang (Instagram, TikTok, Vimeo, Twitter)\n"
            "2. Video manzilini tekshirib ko'ring\n"
            "3. Mahalliy kompyuteringizda botni ishga tushiring\n\n"
            "📢 YouTube hozirda avtomatik yuklab olishni faol cheklamoqda. "
            "Bu xavfsizlik chorasi bo'lib, botlarning tizimdan foydalanishini oldini oladi." +
            railway_msg +
            youtube_solutions +
            "\n\n🔄 Tavsiya: Boshqa platformalardan video yuklab oling. "
            "Instagram, TikTok va Vimeo saytlari YouTube qanday cheklovlarsiz ishlaydi."
        )
    
    async def download_with_youtube_retry(self, url: str, ydl_opts: Dict[str, Any], progress_message) -> Tuple[Dict, str]:
        """YouTube uchun qayta urinish bilan yuklab olish."""
        import yt_dlp
        import asyncio
        import random
        
        # YouTube alternativ metodlari
        youtube_alternatives = self.get_alternative_formats()
        
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
                if self.is_youtube_bot_error(error_msg):
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

# YouTubeHelper obyektini yaratish
youtube_helper = YouTubeHelper()

# Funksiyalarni eksport qilish
__all__ = ['YouTubeHelper', 'youtube_helper']