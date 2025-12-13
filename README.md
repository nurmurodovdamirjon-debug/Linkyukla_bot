# 🎬 Telegram Video Download Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**Turli platformalardan videolarni yuklab olish uchun zamonaviy Telegram bot**

[![GitHub stars](https://img.shields.io/github/stars/DAMIR030303/telegram_video_bot?style=social)](https://github.com/DAMIR030303/telegram_video_bot)
[![GitHub forks](https://img.shields.io/github/forks/DAMIR030303/telegram_video_bot?style=social)](https://github.com/DAMIR030303/telegram_video_bot)

</div>

---

## 📋 **Loyiha haqida**

Bu bot foydalanuvchilarga URL manzilini yuborish orqali turli platformalardan videolarni yuklab olish imkonini beradi. Bot zamonaviy texnologiyalar va kutubxonalar yordamida ishlab chiqilgan.

### ✨ **Asosiy xususiyatlar**

- 🎥 **Ko'p platforma qo'llab-quvvatlash** - YouTube, Instagram, TikTok, Twitter, Vimeo, Facebook
- 🌍 **Tarjima funksiyasi** - Deep Translator bilan avtomatik tarjima
- 📱 **Qulay interfeys** - Inline tugmalar va emoji qo'llab-quvvatlash
- ⚡ **Tez ishlash** - Optimallashtirilgan yuklab olish jarayoni
- 🔒 **Xavfsizlik** - Fayllar avtomatik o'chiriladi
- 📊 **Statistika** - Video ma'lumotlari va ko'rsatkichlar
- 🛡️ **Cheklovlar** - Video hajmi va davomiyligi tekshiruvi

---

## 🚀 **Tezkor boshlash**

### **Talablar**

- Python 3.9 yoki yuqori versiyasi
- Telegram Bot Token
- Internet ulanishi

### **O'rnatish**

1. **Repository'ni klonlang:**
```bash
git clone https://github.com/DAMIR030303/telegram_video_bot.git
cd telegram_video_bot
```

2. **Kerakli kutubxonalarni o'rnating:**
```bash
pip install -r requirements.txt
```

3. **FFmpeg ni o'rnating (Instagram audio ajratish uchun):**
```bash
# Windows
# https://ffmpeg.org/download.html saytidan yuklab oling va PATH ga qo'shing

# MacOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg

# Linux (CentOS/RHEL)
sudo yum install epel-release
sudo yum install ffmpeg
```

4. **Muhit o'zgaruvchilarini sozlang:**
```bash
cp .env.example .env
```

4. **`.env` faylini tahrirlang:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
MAX_VIDEO_DURATION=6000
MAX_VIDEO_SIZE=52428800
DOWNLOAD_DIR=downloads
LOG_LEVEL=INFO
```

5. **Botni ishga tushiring:**
```bash
python run_bot.py
```

### **Railway.ga deploy qilish**

1. **GitHub repository'sini Railway'ga ulang**
2. **Environment variables qo'shing:**
   - `TELEGRAM_BOT_TOKEN` - Telegram bot tokeningiz
   - `COOKIES_CONTENT` - YouTube cookies fayli mazmuni (ixtiyoriy lekin tavsiya etiladi)

3. **Cookies faylini qo'shish (YouTube uchun):**
   - Brauzeringizga "Get cookies.txt" kengaytmasini o'rnating
   - YouTube saytiga kirib, hisobingizga kiring
   - cookies.txt faylini eksport qiling
   - Uni Railway environment variables sifatida qo'shing:
     - Key: `COOKIES_CONTENT`
     - Value: cookies.txt fayli mazmuni

4. **Build command:**
```bash
pip install -r requirements.txt
```

5. **Run command:**
```bash
python run_bot.py
```

---

## 📱 **Ishlatish**

### **Bot bilan ishlash**

1. **Botni boshlang:** `/start`
2. **Yordam oling:** `/help`
3. **Bot haqida:** `/about`
4. **Video URL yuboring:** `https://youtube.com/watch?v=...`

### **Qo'llab-quvvatlanadigan platformalar**

| Platforma | Emoji | Holat |
|-----------|-------|-------|
| YouTube | 🔴 | ✅ To'liq qo'llab-quvvatlanadi |
| Instagram | 📸 | ✅ To'liq qo'llab-quvvatlanadi |
| TikTok | 🎵 | ✅ To'liq qo'llab-quvvatlanadi |
| Twitter/X | 🐦 | ✅ To'liq qo'llab-quvvatlanadi |
| Vimeo | 🔷 | ✅ To'liq qo'llab-quvvatlanadi |
| Facebook | 📘 | ✅ To'liq qo'llab-quvvatlanadi |

---

## 🛠️ **Texnologiyalar**

### **Asosiy kutubxonalar**

- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** - Telegram Bot API
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - Video yuklab olish
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - Muhit o'zgaruvchilari
- **[deep-translator](https://github.com/nidhaloff/deep-translator)** - Tarjima funksiyasi
- **[emoji](https://github.com/carpedm20/emoji)** - Emoji qo'llab-quvvatlash

### **Arxitektura**

```
telegram_video_bot/
├── src/
│   └── bot.py              # Asosiy bot kodi
├── requirements.txt         # Python kutubxonalari
├── run_bot.py              # Ishga tushirish skripti
├── .env.example            # Muhit o'zgaruvchilari namunasi
├── .gitignore              # Git ignore qoidalari
└── README.md               # Loyiha hujjati
```

---

## ⚙️ **Sozlash**

### **Muhim sozlamalar**

| O'zgaruvchi | Tavsif | Standart qiymat |
|-------------|--------|-----------------|
| `TELEGRAM_BOT_TOKEN` | Bot tokeni | **Majburiy** |
| `MAX_VIDEO_DURATION` | Maksimal video davomiyligi (soniya) | `6000` |
| `MAX_VIDEO_SIZE` | Maksimal video hajmi (bayt) | `52428800` |
| `DOWNLOAD_DIR` | Yuklab olish katalogi | `downloads` |
| `LOG_LEVEL` | Log darajasi | `INFO` |

### **Bot tokenini olish**

1. [@BotFather](https://t.me/BotFather) ga kiring
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting
4. Bot username'ini kiriting
5. Token'ni nusxalang

---

## 🔧 **Rivojlantirish**

### **Loyihani klonlang**

```bash
git clone https://github.com/DAMIR030303/telegram_video_bot.git
cd telegram_video_bot
```

### **Virtual muhit yarating**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate     # Windows
```

### **Talablarni o'rnating**

```bash
pip install -r requirements.txt
```

---

## 📊 **Funksiyalar**

### **Asosiy funksiyalar**

- ✅ **Video yuklab olish** - Turli platformalardan
- ✅ **Platforma aniqlash** - Avtomatik platforma taniqlash
- ✅ **Tarjima** - Video izohlarini tarjima qilish
- ✅ **Statistika** - Video ko'rsatkichlari
- ✅ **Cheklovlar** - Hajm va davomiylik tekshiruvi
- ✅ **Xatolik boshqaruvi** - Batafsil xato xabarlari

---

## 🚨 **Cheklovlar**

### **Telegram cheklovlari**

- 📏 **Maksimal fayl hajmi:** 50MB
- ⏱️ **Maksimal video davomiyligi:** 100 daqiqa
- 🔒 **Xavfsizlik:** Shaxsiy videolarni yuklab olmaydi

### **Platforma cheklovlari**

- 🚫 **Mover.uz** - Qo'llab-quvvatlanmaydi
- 🔒 **Shaxsiy videolar** - Faqat ochiq videolar
- 🌍 **Mintaqaviy cheklovlar** - Ba'zi videolar mintaqaviy cheklangan

---

## 🐛 **Muammolarni hal qilish**

### **Tez-tez uchraydigan muammolar**

<details>
<summary><b>❌ "ModuleNotFoundError"</b></summary>

```bash
pip install -r requirements.txt
```

</details>

<details>
<summary><b>❌ "TELEGRAM_BOT_TOKEN not found"</b></summary>

`.env` faylining mavjudligini va to'g'ri sozlanganligini tekshiring.

</details>

<details>
<summary><b>❌ "Unsupported URL"</b></summary>

URL manzil to'g'ri ekanligini tekshiring. Faqat qo'llab-quvvatlanadigan platformalar.

</details>

<details>
<summary><b>❌ "HTTP Error 403"</b></summary>

Video ochiq ekanligini tekshiring. Shaxsiy yoki cheklangan videolar yuklab olinmaydi.

</details>

<details>
<summary><b>❌ "Sign in to confirm you're not a bot" (YouTube)</b></summary>

YouTube hozirda avtomatik yuklab olishni cheklamoqda. Bu xavfsizlik chorasi bo'lib, botlarning tizimdan foydalanishini oldini oladi.

**Yechimlar:**
1. **cookies.txt faylini yaratish:**
   - Brauzeringizga "Get cookies.txt" kengaytmasini o'rnatish
   - YouTube saytiga kirib, hisobingizga kiring
   - cookies.txt faylini eksport qiling
   - Uni bot katalogiga joylashtiring

2. **Muqobil platformalardan foydalaning:**
   - Vimeo, Instagram, TikTok kabi boshqa platformalardan video yuklab oling

3. **Video manzilini tekshiring:**
   - URL to'g'ri ekanligiga ishonch hosil qiling
</details>

### YouTube Bot Tekshiruvini Chetlab O'tish

YouTube hozirda avtomatik yuklab olishni faol cheklamoqda. Bu xavfsizlik chorasi bo'lib, botlarning tizimdan foydalanishini oldini oladi.

#### Yechimlar:

1. **Cookies faylidan foydalanish** (Eng samarali)
2. **Proxy serverdan foydalanish**
3. **Mahalliy kompyuteringizda botni ishga tushirish**

##### 1. Cookies faylini yaratish:

YouTube cookies faylini olish uchun:

1. Brauzeringizga "Get cookies.txt" kengaytmasini o'rnating
2. YouTube saytiga kiring va hisobingizga kiring
3. Har qanday YouTube sahifasini oching
4. Kengaytmani ishga tushiring va cookies faylini eksport qiling
5. Uni `cookies.txt` sifatida saqlang va bot jildiga joylashtiring

##### 2. Proxy serverdan foydalanish:

Agar proxy serveringiz bo'lsa:
```env
HTTP_PROXY=http://proxy_server:port
HTTPS_PROXY=https://proxy_server:port
```

##### 3. Mahalliy kompyuteringizda ishga tushirish:

YouTube cheklovlari ko'pincha cloud hostinglardagi IP manzillarga qo'llaniladi.
Mahalliy kompyuteringizning IP manzili cheklanmagan bo'lishi ehtimoliy.

---

## 📈 **Kelajakdagi rejalar**

- [ ] **Cloud storage integratsiyasi** - Google Drive, Dropbox
- [ ] **Video qismlarga bo'lish** - Katta videolarni qismlarga bo'lish
- [ ] **Playlist qo'llab-quvvatlash** - Butun playlist yuklab olish
- [ ] **Audio yuklab olish** - Faqat audio fayllar
- [ ] **Web interfeys** - Brauzer orqali ishlatish
- [ ] **API** - Boshqa dasturlar bilan integratsiya

---

## 🤝 **Hissa qo'shish**

Bizning loyihaga hissa qo'shishni xohlasangiz:

1. **Fork qiling** - Repository'ni fork qiling
2. **Branch yarating** - `git checkout -b feature/amazing-feature`
3. **Commit qiling** - `git commit -m 'Add amazing feature'`
4. **Push qiling** - `git push origin feature/amazing-feature`
5. **Pull Request yarating** - GitHub'da Pull Request oching

### **Kod yozish qoidalari**

- **PEP 8** standartlariga amal qiling
- **Docstring** yozing
- **Test** yozing
- **README** yangilang

---

## 📞 **Yordam va aloqa**

### **Yordam olish**

- 📧 **Email:** [damir@example.com](mailto:damir@example.com)
- 💬 **Telegram:** [@damir_dev](https://t.me/damir_dev)
- 🐛 **Issues:** [GitHub Issues](https://github.com/DAMIR030303/telegram_video_bot/issues)

### **Ijodiy jamoa**

- 👨‍💻 **Dasturchi:** N.Damir - Senior Developer

---

## 📄 **Litsenziya**

Bu loyiha MIT litsenziyasi ostida tarqatiladi. Batafsil ma'lumot uchun [LICENSE](LICENSE) faylini ko'ring.

---

## ⭐ **Yulduzcha qo'shing**

Agar loyiha sizga yoqsa, yulduzcha qo'shing va repository'ni kuzatib boring!

[![GitHub stars](https://img.shields.io/github/stars/DAMIR030303/telegram_video_bot?style=social)](https://github.com/DAMIR030303/telegram_video_bot)

---

<div align="center">

**Made with ❤️ by [N.Damir](https://github.com/DAMIR030303)**

[![GitHub](https://img.shields.io/badge/GitHub-DAMIR030303-black?style=for-the-badge&logo=github)](https://github.com/DAMIR030303)
[![Telegram](https://img.shields.io/badge/Telegram-@damir_dev-blue?style=for-the-badge&logo=telegram)](https://t.me/damir_dev)

</div>
