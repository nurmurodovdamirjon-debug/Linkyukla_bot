# Linkyukla Bot - Telegram Video Downloader

A modern Telegram bot for downloading videos from multiple platforms directly to Telegram.

## 🚀 Features

- **Multi-Platform Support**: YouTube, Instagram, TikTok, Twitter/X, Vimeo, Facebook
- **Auto Platform Detection**: Automatically detects the platform from URL
- **Inline Keyboard UI**: Beautiful platform selection buttons with emojis
- **Video Metadata**: Title, description, duration displayed in captions
- **Auto-Translation**: Captions/descriptions translated to Uzbek using Deep Translator
- **Audio Extraction**: FFmpeg-based audio extraction (Instagram)
- **File Size Validation**: Enforces Telegram's 50MB limit
- **Duration Validation**: Enforces max duration limit (default 100 minutes)
- **YouTube Cookie Auth**: Supports cookies.txt for YouTube bot detection bypass
- **Retry Logic**: Multiple download attempts with alternative formats
- **Health Check Server**: HTTP endpoint for cloud platform monitoring
- **Automatic Cleanup**: Downloaded files removed after sending
- **Comprehensive Logging**: Detailed logging for debugging

## 📋 Supported Platforms

| Platform | Emoji | Example URL |
|----------|-------|-------------|
| YouTube | 🔴 | https://www.youtube.com/watch?v=example |
| Instagram | 📸 | https://www.instagram.com/p/example/ |
| TikTok | 🎵 | https://www.tiktok.com/@user/video/example |
| Twitter/X | 🐦 | https://twitter.com/user/status/example |
| Vimeo | 🔷 | https://vimeo.com/example |
| Facebook | 📘 | https://www.facebook.com/user/videos/example |

## 🛠 Installation

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Linkyukla_bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required for audio extraction and format merging):
   - **Windows**: Download from https://ffmpeg.org/download.html
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Telegram bot token.

5. **Run the bot:**
   ```bash
   python run_bot.py
   ```

### Docker Installation

1. **Build the Docker image:**
   ```bash
   docker build -t linkyukla-bot .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     -e TELEGRAM_BOT_TOKEN=your_token_here \
     -v $(pwd)/downloads:/app/downloads \
     linkyukla-bot
   ```

### Cloud Deployment (Koyeb/Railway)

1. **Set environment variables:**
   - `TELEGRAM_BOT_TOKEN` (required)
   - `MAX_VIDEO_DURATION` (optional, default: 6000)
   - `MAX_VIDEO_SIZE` (optional, default: 52428800)
   - `LOG_LEVEL` (optional, default: INFO)
   - `PORT` (optional, default: 8000)

2. **Deploy** using your cloud provider's dashboard or CLI.

3. **Health check** is automatically available on `/` endpoint.

## ⚙️ Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token from @BotFather | - | ✅ Yes |
| `MAX_VIDEO_DURATION` | Maximum video duration in seconds | `6000` | ❌ No |
| `MAX_VIDEO_SIZE` | Maximum file size in bytes | `52428800` (50MB) | ❌ No |
| `DOWNLOAD_DIR` | Directory for temporary downloads | `downloads` | ❌ No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | ❌ No |
| `COOKIES_CONTENT` | YouTube cookies content for auth bypass | - | ❌ No |
| `HTTP_PROXY` | HTTP proxy URL | - | ❌ No |
| `HTTPS_PROXY` | HTTPS proxy URL | - | ❌ No |
| `PORT` | Health check server port | `8000` | ❌ No |

## 📖 Usage

1. **Start the bot:** Send `/start` command
2. **Select platform:** Click on platform button (optional)
3. **Send URL:** Paste video URL from supported platform
4. **Download:** Bot will process and send the video

### Commands

- `/start` - Welcome message with platform selection
- `/help` - Usage instructions
- `/about` - Bot information and credits

## 🧪 Testing

Run the test suite:

```bash
# Install pytest (if not installed)
pip install pytest

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src
```

### Test Coverage

The test suite includes:
- Platform detection tests
- URL validation tests
- Filename sanitization tests
- Platform emoji/button tests
- Constants validation tests

## 📁 Project Structure

```
Linkyukla_bot/
├── src/
│   ├── __init__.py          # Package initializer
│   ├── bot.py               # Main bot logic
│   ├── youtube_helper.py    # YouTube-specific helper
│   ├── buttons.py           # Inline keyboard handler
│   └── constants.py         # Project-wide constants
├── tests/
│   ├── __init__.py          # Test package
│   └── test_bot.py          # Unit tests
├── downloads/               # Temporary download directory
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── run_bot.py               # Entry point script
├── Dockerfile               # Docker configuration
├── README.md                # Documentation (Uzbek)
├── README.en.md             # Documentation (English)
└── LICENSE                  # MIT License
```

## 🔧 Troubleshooting

### YouTube Bot Detection

YouTube actively blocks automated downloads. If you encounter errors:

1. **Add cookies.txt**: Export cookies from your browser and add to `COOKIES_CONTENT`
2. **Use proxy**: Set `HTTP_PROXY` or `HTTPS_PROXY` environment variable
3. **Try alternative platforms**: Instagram, TikTok, Vimeo work without restrictions

### FFmpeg Not Found

If you see "FFmpeg topilmadi" warning:

- **Windows**: Download from https://ffmpeg.org/download.html and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### File Too Large

Telegram has a 50MB file size limit. If video is larger:

- Bot will automatically reject files > 50MB
- Consider using lower quality formats

## 📝 Dependencies

- **python-telegram-bot** >= 22.0 - Telegram Bot API framework
- **python-dotenv** >= 1.0.0 - Environment variable management
- **deep-translator** >= 1.11.4 - Auto-translation for captions
- **emoji** >= 2.8.0 - Emoji support for UI
- **ffmpeg-python** >= 0.2.0 - FFmpeg bindings for audio extraction
- **yt-dlp** (from GitHub) - Video downloader
- **yt-dlp-ejs** >= 0.8.0 - JavaScript runtime for yt-dlp

## 🔒 Privacy

- No video or personal data is stored on servers
- All processing is temporary
- Files are deleted after sending to user
- Logs only contain metadata (user ID, URL, timestamps)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**N.Damir** - Senior Developer

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact the author directly

## 🗺 Roadmap

- [ ] Add more platform support
- [ ] Implement video quality selection
- [ ] Add playlist download support
- [ ] Implement user preferences
- [ ] Add statistics and analytics
- [ ] Multi-language support (beyond Uzbek)

---

*Last updated: March 2026*
