#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Button Handler - Telegram bot uchun tugma bosilganda ishlov berish
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# Import constants to avoid duplicate code
from src.constants import (
    WELCOME_MESSAGE,
    PLATFORM_EMOJIS,
    PLATFORM_NAMES,
    PLATFORM_EXAMPLE_URLS,
    MAIN_MENU_KEYBOARD,
)

# Logger yaratish
logger = logging.getLogger(__name__)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tugma bosilganda ishlov berish."""
    try:
        query = update.callback_query
        
        # ✅ HIGH: callback_query null check
        if not query:
            logger.warning("callback_query is None")
            return
        
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
            platform_name = PLATFORM_NAMES.get(platform, platform.capitalize())
            example_url = PLATFORM_EXAMPLE_URLS.get(platform, 'https://example.com')

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
            # Asosiy menyuga qaytish - constants dan foydalanish (duplicate code oldini olish)
            welcome_message = WELCOME_MESSAGE.format(name=user.first_name)
            reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)

            await query.edit_message_text(welcome_message, reply_markup=reply_markup)

        # Instagram uchun maxsus tugmalar
        elif data.startswith("insta_"):
            action_parts = data.split("_")
            action = action_parts[1]  # "video" yoki "both"

            if action == "both":
                # Video + Audio
                await query.edit_message_text("🎵 Instagram videodan audio ajratish jarayoni boshlanmoqda...")
                await query.message.reply_text(
                    "🎵 Instagram videodan audio ajratish funksiyasi hozircha mavjud emas.\n"
                    "Iltimos, oddiy video yuboring."
                )
            elif action == "video":
                # Faqat video
                await query.edit_message_text("📹 Faqat video yuborilmoqda...")
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

    except BadRequest as e:
        # ✅ HIGH: Specific Telegram error handling
        if "Message is not modified" in str(e):
            logger.debug("Message already modified, skipping")
        elif "Message can't be edited" in str(e):
            logger.debug("Message can't be edited")
        else:
            logger.error(f"Telegram BadRequest: {str(e)}")
            try:
                await query.message.reply_text(
                    "❌ Tugma bosilganda xatolik yuz berdi.\n"
                    "Iltimos, video URL manzilini bevosita yuboring."
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Tugma bosilganda xatolik: {str(e)}", exc_info=True)
        try:
            await query.edit_message_text(
                "❌ Tugma bosilganda xatolik yuz berdi.\n"
                "Iltimos, video URL manzilini bevosita yuboring."
            )
        except Exception:
            pass


__all__ = ['button_handler']
