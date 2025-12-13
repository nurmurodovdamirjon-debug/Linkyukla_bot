#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Button Handler - Telegram bot uchun tugma bosilganda ishlov berish
"""

import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Logger yaratish
logger = logging.getLogger(__name__)

# Global o'zgaruvchilar
instagram_video_files = {}  # {user_id: {'video': video_filename, 'info': info_dict}}

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tugma bosilganda ishlov berish."""
    try:
        query = update.callback_query
        await query.answer()
        
        if not query.data:
            await query.edit_message_text("❌ Tugma ma'lumotlari topilmadi.")
            return
            
        data = query.data
        user = query.from_user
        
        logger.info(f"Foydalanuvchi {user.first_name} ({user.id}) tugmasini bosdi: {data}")
        
        # Platforma tanlash tugmalari
        if data.startswith("platform_"):
            platform = data[9:]  # "platform_" dan keyingi qism
            platform_names = {
                'youtube': 'YouTube',
                'instagram': 'Instagram',
                'tiktok': 'TikTok',
                'twitter': 'Twitter',
                'vimeo': 'Vimeo',
                'facebook': 'Facebook'
            }
            platform_name = platform_names.get(platform, platform.capitalize())
            
            example_urls = {
                'youtube': 'https://www.youtube.com/watch?v=example',
                'instagram': 'https://www.instagram.com/p/example/',
                'tiktok': 'https://www.tiktok.com/@user/video/example',
                'twitter': 'https://twitter.com/user/status/example',
                'vimeo': 'https://vimeo.com/example',
                'facebook': 'https://www.facebook.com/user/videos/example'
            }
            example_url = example_urls.get(platform, 'https://example.com')
            
            message = (
                f"📥 {platform_name} platformasidan video yuklab olish\n\n"
                f"Quyidagi formatda URL manzil yuboring:\n"
                f"{example_url}\n\n"
                f"Masalan: {example_url}"
            )
            
            # Orqaga qaytish tugmasi
            keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
            
        elif data == "back_to_main":
            # Asosiy menyuga qaytish
            welcome_message = (
                f"👋 Salom {user.first_name}!\n\n"
                "Men turli platformalardan videolarni yuklab olishga yordam beradigan zamonaviy video botiman.\n\n"
                "📥 Menga video URL manzilini yuboring va men uni siz uchun yuklab olaman.\n"
                "✅ Qo'llab-quvvatlanadigan platformalar:\n"
                "• 🟥 YouTube\n"
                "• 📸 Instagram\n"
                "• 🎵 TikTok\n"
                "• 🐦 Twitter/X\n"
                "• 🔷 Vimeo\n"
                "• 📘 Facebook\n\n"
                "⚠️ Eslatma: Telegram cheklovlari tufayli 50MB dan katta videolar maxsus usullar bilan yuboriladi.\n\n"
                "👨‍💻 Dastur muallifi: N.Damir - Senior Dasturchi"
            )
            
            # Platforma tanlash tugmalari
            keyboard = [
                [InlineKeyboardButton("🔴 YouTube", callback_data="platform_youtube")],
                [InlineKeyboardButton("📸 Instagram", callback_data="platform_instagram")],
                [InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok")],
                [InlineKeyboardButton("🐦 Twitter", callback_data="platform_twitter")],
                [InlineKeyboardButton("🔷 Vimeo", callback_data="platform_vimeo")],
                [InlineKeyboardButton("📘 Facebook", callback_data="platform_facebook")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(welcome_message, reply_markup=reply_markup)
            
        # Instagram uchun maxsus tugmalar
        elif data.startswith("insta_"):
            action_parts = data.split("_")
            action = action_parts[1]  # "video" yoki "both"
            user_id = user.id
            
            if action == "both":
                # Video + Audio
                await query.edit_message_text("🎵 Instagram videodan audio ajratish jarayoni boshlanmoqda...")
                # Bu yerda video + audio ajratish logikasi bo'ladi
                # Hozircha oddiy xabar
                await query.message.reply_text(
                    "🎵 Instagram videodan audio ajratish funksiyasi hozircha mavjud emas.\n"
                    "Iltimos, oddiy video yuboring."
                )
            elif action == "video":
                # Faqat video
                await query.edit_message_text("📹 Faqat video yuborilmoqda...")
                # Bu yerda faqat video yuborish logikasi bo'ladi
                # Hozircha oddiy xabar
                await query.message.reply_text(
                    "📹 Faqat video yuborish funksiyasi hozircha mavjud emas.\n"
                    "Iltimos, video URL manzilini bevosita yuboring."
                )
                
        else:
            # Noma'lum tugma
            await query.edit_message_text(
                "❌ Bu funksiya hozircha mavjud emas.\n"
                "Iltimos, video URL manzilini bevosita yuboring."
            )
            
    except Exception as e:
        logger.error(f"Tugma bosilganda xatolik: {str(e)}")
        try:
            await query.edit_message_text(
                "❌ Tugma bosilganda xatolik yuz berdi.\n"
                "Iltimos, video URL manzilini bevosita yuboring."
            )
        except:
            pass

# Funksiyani eksport qilish
__all__ = ['button_handler', 'instagram_video_files']