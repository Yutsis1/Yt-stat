# YouTube Comment Analyzer Bot 🎬📊

A Telegram bot that analyzes YouTube video comments using AI to identify:
- **Dominant comment types** - What kind of comments appear most frequently
- **Most liked comment types** - What kind of comments receive the most engagement

## Features

- 🔗 Supports multiple YouTube URL formats
- 💬 Fetches top 100 comments sorted by relevance
- 🤖 Uses ChatGPT (GPT-4o-mini) for intelligent categorization
- 📊 Beautiful formatted analysis reports
- ⚡ Fast async processing with FastAPI

## Setup

### 1. Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- YouTube Data API Key (from [Google Cloud Console](https://console.cloud.google.com/apis/credentials))
- OpenAI API Key (from [OpenAI Platform](https://platform.openai.com/api-keys))

### 2. Installation

```bash
# Clone and enter the project
cd Yt-stat

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
```

Required environment variables:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `YOUTUBE_API_KEY` - YouTube Data API v3 key
- `OPENAI_API_KEY` - OpenAI API key
- `COMMENT_PROMPT_ID` - OpenAI Prompt ID (if you use prompt library features)

### 4. Running the Bot

#### Development (Polling Mode)

```bash
python run_polling.py
```

#### Production (Webhook Mode)

Set `WEBHOOK_URL` in your `.env` file, then:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Usage

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Paste any YouTube video URL
4. Wait 10-30 seconds for the analysis
5. Receive a detailed breakdown of comment types!


## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/webhook` | POST | Telegram webhook receiver |

## License

MIT
