# -*- coding: utf-8 -*-
"""
Linkyukla Bot Tests
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bot import (
    detect_platform,
    is_valid_url,
    sanitize_filename,
    get_platform_sticker,
    get_platform_button_text,
)
from src.constants import (
    PLATFORM_EMOJIS,
    PLATFORM_NAMES,
    CAPTION_MAX_LENGTH,
    MAX_VIDEO_SIZE,
    MAX_VIDEO_DURATION,
)


class TestDetectPlatform:
    """detect_platform() funksiyasi testlari"""

    def test_detect_youtube(self):
        """YouTube URL aniqlash"""
        assert detect_platform('https://www.youtube.com/watch?v=abc123') == 'youtube'
        assert detect_platform('https://youtu.be/abc123') == 'youtube'
        assert detect_platform('http://youtube.com/watch?v=xyz') == 'youtube'

    def test_detect_instagram(self):
        """Instagram URL aniqlash"""
        assert detect_platform('https://www.instagram.com/p/abc123/') == 'instagram'
        assert detect_platform('https://instagr.am/p/xyz/') == 'instagram'

    def test_detect_tiktok(self):
        """TikTok URL aniqlash"""
        assert detect_platform('https://www.tiktok.com/@user/video/123456') == 'tiktok'
        assert detect_platform('https://tiktok.com/@test/video/abc') == 'tiktok'

    def test_detect_twitter(self):
        """Twitter/X URL aniqlash"""
        assert detect_platform('https://twitter.com/user/status/123456') == 'twitter'
        assert detect_platform('https://x.com/user/status/abc') == 'twitter'

    def test_detect_vimeo(self):
        """Vimeo URL aniqlash"""
        assert detect_platform('https://vimeo.com/123456') == 'vimeo'
        assert detect_platform('https://www.vimeo.com/abc') == 'vimeo'

    def test_detect_facebook(self):
        """Facebook URL aniqlash"""
        assert detect_platform('https://www.facebook.com/user/videos/123') == 'facebook'
        assert detect_platform('https://fb.com/video/abc') == 'facebook'

    def test_detect_unknown(self):
        """Noma'lum platformani aniqlash"""
        assert detect_platform('https://example.com/video') == 'unknown'
        assert detect_platform('not_a_url') == 'unknown'


class TestIsValidUrl:
    """is_valid_url() funksiyasi testlari"""

    def test_valid_https_url(self):
        """HTTPS URL haqiqiyligini tekshirish"""
        assert is_valid_url('https://www.youtube.com/watch?v=abc') == True
        assert is_valid_url('https://example.com') == True

    def test_valid_http_url(self):
        """HTTP URL haqiqiyligini tekshirish"""
        assert is_valid_url('http://example.com') == True
        assert is_valid_url('http://www.youtube.com') == True

    def test_invalid_url_no_scheme(self):
        """Scheme'siz URL - noto'g'ri"""
        assert is_valid_url('example.com') == False
        assert is_valid_url('youtube.com') == False

    def test_invalid_url_empty(self):
        """Bo'sh string - noto'g'ri"""
        assert is_valid_url('') == False

    def test_invalid_url_not_url(self):
        """URL bo'lmagan matn"""
        assert is_valid_url('not_a_url') == False
        assert is_valid_url('hello world') == False


class TestSanitizeFilename:
    """sanitize_filename() funksiyasi testlari"""

    def test_remove_special_chars(self):
        """Maxsus belgilarni olib tashlash"""
        assert sanitize_filename('test<>:"file') == 'test____file'
        assert sanitize_filename('file|?*name') == 'file___name'

    def test_multiple_spaces(self):
        """Ko'p bo'sh joylarni bittaga qisqartirish"""
        assert sanitize_filename('test    file') == 'test file'
        assert sanitize_filename('multiple   spaces   here') == 'multiple spaces here'

    def test_trim_length(self):
        """Fayl nomini 150 belgigacha qisqartirish"""
        long_name = 'a' * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 150

    def test_normal_filename(self):
        """Oddiy fayl nomi"""
        assert sanitize_filename('normal_file.mp4') == 'normal_file.mp4'
        assert sanitize_filename('My Video 2024.mp4') == 'My Video 2024.mp4'


class TestGetPlatformSticker:
    """get_platform_sticker() funksiyasi testlari"""

    def test_youtube_sticker(self):
        """YouTube stikeri"""
        assert get_platform_sticker('youtube') == '🔴'

    def test_instagram_sticker(self):
        """Instagram stikeri"""
        assert get_platform_sticker('instagram') == '📸'

    def test_tiktok_sticker(self):
        """TikTok stikeri"""
        assert get_platform_sticker('tiktok') == '🎵'

    def test_twitter_sticker(self):
        """Twitter stikeri"""
        assert get_platform_sticker('twitter') == '🐦'

    def test_vimeo_sticker(self):
        """Vimeo stikeri"""
        assert get_platform_sticker('vimeo') == '🔷'

    def test_facebook_sticker(self):
        """Facebook stikeri"""
        assert get_platform_sticker('facebook') == '📘'

    def test_unknown_sticker(self):
        """Noma'lum platforma stikeri"""
        assert get_platform_sticker('unknown') == '❓'
        assert get_platform_sticker('invalid') == '❓'


class TestGetPlatformButtonText:
    """get_platform_button_text() funksiyasi testlari"""

    def test_youtube_button(self):
        """YouTube tugma matni"""
        assert get_platform_button_text('youtube') == 'YouTube Videosi'

    def test_instagram_button(self):
        """Instagram tugma matni"""
        assert get_platform_button_text('instagram') == 'Instagram Videosi'

    def test_tiktok_button(self):
        """TikTok tugma matni"""
        assert get_platform_button_text('tiktok') == 'TikTok Videosi'

    def test_unknown_button(self):
        """Noma'lum platforma tugma matni"""
        assert get_platform_button_text('unknown') == 'Video'


class TestConstants:
    """Constants fayli testlari"""

    def test_max_video_size(self):
        """MAX_VIDEO_SIZE 50MB ekanligini tekshirish"""
        assert MAX_VIDEO_SIZE == 50 * 1024 * 1024
        assert MAX_VIDEO_SIZE == 52428800

    def test_max_video_duration(self):
        """MAX_VIDEO_DURATION 6000 soniya (100 daqiqa) ekanligini tekshirish"""
        assert MAX_VIDEO_DURATION == 6000
        assert MAX_VIDEO_DURATION // 60 == 100

    def test_caption_max_length(self):
        """CAPTION_MAX_LENGTH 1024 belgi ekanligini tekshirish (Telegram limiti)"""
        assert CAPTION_MAX_LENGTH == 1024

    def test_platform_emojis_complete(self):
        """Barcha platformalar uchun emoji borligini tekshirish"""
        required_platforms = ['youtube', 'instagram', 'tiktok', 'twitter', 'vimeo', 'facebook', 'unknown']
        for platform in required_platforms:
            assert platform in PLATFORM_EMOJIS
            assert isinstance(PLATFORM_EMOJIS[platform], str)

    def test_platform_names_complete(self):
        """Barcha platformalar uchun nom borligini tekshirish"""
        required_platforms = ['youtube', 'instagram', 'tiktok', 'twitter', 'vimeo', 'facebook', 'unknown']
        for platform in required_platforms:
            assert platform in PLATFORM_NAMES
            assert isinstance(PLATFORM_NAMES[platform], str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
