#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Helper - YouTube uchun maxsus algoritmlar va yechimlar
"""

import logging
import os
import random
import asyncio
from typing import Dict, Any, Tuple

import yt_dlp

# Import constants to avoid magic numbers and duplicate code
from src.constants import (
    YT_DLP_SLEEP_INTERVAL,
    YT_DLP_MAX_SLEEP_INTERVAL,
    YT_DLP_RETRIES,
    SOCKET_TIMEOUT,
    FRAGMENT_RETRIES,
    YOUTUBE_ALTERNATIVE_FORMATS,
    YOUTUBE_BOT_ERROR_MESSAGE,
)

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
        ]

        self.referers = [
            'https://www.google.com/',
            'https://www.youtube.com/',
            'https://duckduckgo.com/',
        ]

        self.accept_languages = [
            'en-US,en;q=0.9',
            'ru-RU,ru;q=0.9',
            'uz-UZ,uz;q=0.9',
        ]

    def get_youtube_headers(self) -> Dict[str, str]:
        """YouTube uchun headerlar qaytarish."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(self.accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': random.choice(self.referers),
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
        }

    def get_youtube_options(self, url: str) -> Dict[str, Any]:
        """YouTube uchun yt-dlp opsiyalarini qaytarish."""
        options = {
            'format': 'best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'sleep_interval': YT_DLP_SLEEP_INTERVAL,
            'max_sleep_interval': YT_DLP_MAX_SLEEP_INTERVAL,
            'retries': YT_DLP_RETRIES,
            'fragment_retries': FRAGMENT_RETRIES,
            'socket_timeout': SOCKET_TIMEOUT,
            'http_headers': self.get_youtube_headers(),
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'noplaylist': True,
            # ✅ MEDIUM: js_runtimes deprecated - olib tashlandi
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv', 'web'],
                }
            },
            'ignoreerrors': True,
        }

        self._add_cookies_to_options(options)
        return options

    def get_alternative_formats(self) -> list:
        """
        YouTube uchun alternativ formatlar.
        ✅ P1: Lambda memory leak tuzatildi - constants dan foydalanamiz
        """
        return YOUTUBE_ALTERNATIVE_FORMATS

    def apply_alternative_format(self, opts: dict, index: int) -> dict:
        """
        Alternativ formatni qo'llash.
        ✅ P1: Lambda o'rniga dict merge ishlatamiz
        """
        if 0 <= index < len(YOUTUBE_ALTERNATIVE_FORMATS):
            return dict(opts, **YOUTUBE_ALTERNATIVE_FORMATS[index])
        return opts

    def _add_cookies_to_options(self, options: Dict[str, Any]) -> None:
        """YouTube cookies faylini opsiyalarga qo'shish (bot.py dagi markaziy funksiyadan foydalanadi)."""
        from src.bot import cookie_manager
        cookies_path = cookie_manager.get_path()
        if cookies_path:
            options['cookiefile'] = cookies_path

    def is_youtube_bot_error(self, error_msg: str) -> bool:
        """YouTube bot xatosini aniqlash."""
        error_msg_lower = error_msg.lower()
        youtube_indicators = [
            'bot',
            '429',
            "confirm you're not a bot",
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
        """
        YouTube bot xatolari uchun maxsus xabar.
        ✅ P1: Constants dan foydalanamiz
        """
        railway_msg = ""
        if os.getenv('RAILWAY_ENVIRONMENT'):
            railway_msg = (
                "\n\n📍 Railway deployment aniqlandi. "
                "Ehtimol, Railway IP manzillari YouTube tomonidan cheklangan."
            )

        return YOUTUBE_BOT_ERROR_MESSAGE + railway_msg

    async def download_with_youtube_retry(self, url: str, ydl_opts: Dict[str, Any], progress_message) -> Tuple[Dict, str]:
        """YouTube uchun qayta urinish bilan yuklab olish."""
        youtube_alternatives = self.get_alternative_formats()
        max_attempts = 3
        attempt = 0
        delay_strategies = [1, 3, 5]
        alt_index = 0
        last_exception = None

        while attempt < max_attempts:
            try:
                if attempt > 0:
                    delay = random.choice(delay_strategies)
                    logger.info(f"YouTube uchun {delay} soniya kutish (urinish: {attempt + 1})")
                    await asyncio.sleep(delay)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"Video yuklab olishga harakat qilinmoqda: {url}")
                    info_dict = ydl.extract_info(url, download=True)
                    
                    # ✅ HIGH: info_dict validation after download
                    if info_dict is None:
                        raise yt_dlp.DownloadError("Video ma'lumotlarini olish imkonsiz", video_id=url)
                    
                    video_filename = ydl.prepare_filename(info_dict)
                    logger.info(f"Video muvaffaqiyatli yuklab olindi: {video_filename}")
                return info_dict, video_filename

            except yt_dlp.DownloadError as e:
                attempt += 1
                error_msg = str(e).lower()
                last_exception = e
                logger.error(f"Yuklab olish xatosi (urinish {attempt}): {error_msg}")

                if self.is_youtube_bot_error(error_msg):
                    if alt_index < len(youtube_alternatives):
                        # ✅ P1: Lambda o'rniga apply_alternative_format ishlatish
                        ydl_opts = self.apply_alternative_format(ydl_opts, alt_index)
                        alt_index += 1
                        attempt = 0
                        await progress_message.edit_text("🎵 YouTube cheklovi uchun alternativ usul sinab ko'rilmoqda...")
                        logger.info(f"YouTube uchun alternativ format sinab ko'rilmoqda (index: {alt_index})")
                    else:
                        # ✅ HIGH: Preserve original exception with context
                        logger.error(f"Barcha urinishlar muvaffaqiyatsiz: {error_msg}")
                        raise
                elif attempt >= max_attempts:
                    # ✅ HIGH: Preserve original exception
                    raise
                else:
                    logger.info(f"Qayta urinish uchun kutish: {attempt + 1}/{max_attempts}")

        # ✅ HIGH: Raise original exception with context
        if last_exception:
            raise last_exception
        raise Exception("YouTube videoni yuklab olishda barcha urinishlar muvaffaqiyatsiz tugadi")


# YouTubeHelper obyektini yaratish
youtube_helper = YouTubeHelper()

__all__ = ['YouTubeHelper', 'youtube_helper']
