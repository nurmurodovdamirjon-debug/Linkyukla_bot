#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Video Bot - Ishga tushirish skripti
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def check_python_version():
    """Python versiyasini tekshirish."""
    if sys.version_info < (3, 9):
        print("Xato: Python 3.9 yoki yuqori versiyasi talab qilinadi!")
        print(f"Sizning Python versiyangiz: {sys.version}")
        return False
    return True

def check_requirements():
    """Talablarni tekshirish."""
    try:
        import telegram
        import yt_dlp
        import dotenv
        print("Barcha kerakli kutubxonalar mavjud")
        return True
    except ImportError as e:
        print(f"Xato: Ba'zi kerakli kutubxonalar yetishmayapti: {e}")
        return False

def check_env_file():
    """.env faylini tekshirish."""
    if not os.path.exists('.env'):
        print("Xato: .env fayli topilmadi!")
        return False
    
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token or token == 'YOUR_BOT_TOKEN_HERE':
        print("Xato: TELEGRAM_BOT_TOKEN .env faylida sozlanmagan!")
        print("Iltimos, .env faylini tahrirlang va haqiqiy bot tokenini kiriting.")
        return False
    
    print(".env fayli to'g'ri sozlangan")
    return True

def install_requirements():
    """Talablarni o'rnatish."""
    print("Talablarni o'rnatish...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Barcha talablar muvaffaqiyatli o'rnatildi")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Talablarni o'rnatishda xatolik yuz berdi: {e}")
        return False

def main():
    """Asosiy funksiya."""
    print("Telegram Video Yuklab Olish Botini Ishga Tushirish")
    print("=" * 50)
    
    # Ishchi katalogni o'zgartirish
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Tekshiruvlarni bajarish
    if not check_python_version():
        sys.exit(1)
    
    # Agar talablar yetishmasa, ularni o'rnatish
    if not check_requirements():
        print("\nTalablarni o'rnatish kerakmi? (y/n): ", end="")
        if input().lower() == 'y':
            if not install_requirements():
                sys.exit(1)
        else:
            print("Iltimos, avval talablarni o'rnating: pip install -r requirements.txt")
            sys.exit(1)
    
    # .env faylini tekshirish
    if not check_env_file():
        sys.exit(1)
    
    # Botni ishga tushirish
    print("\nBot ishga tushirilmoqda...")
    try:
        from src.bot import main as bot_main
        bot_main()
    except Exception as e:
        print(f"Botni ishga tushirishda xatolik yuz berdi: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
