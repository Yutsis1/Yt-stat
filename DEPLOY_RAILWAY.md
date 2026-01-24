Overview

This repository contains two services that can be deployed to Railway:
- `app` (FastAPI) — Dockerfile: `app/Dockerfile.app`
- `bot` (Telegram bot) — Dockerfile: `bot/Dockerfile.bot`

Quick steps to deploy on Railway

1. Create two services in Railway (one for each service).
2. For each service, choose "Deploy from GitHub" and select this repository.
3. For each service, point Railway to the right Dockerfile path:
   - `app` service: `app/Dockerfile.app`
   - `bot` service: `bot/Dockerfile.bot`
4. Set required environment variables (see list below).
5. For the `app` service, Railway will set `PORT` automatically. The `app` Dockerfile uses `${PORT:-8000}` fallback.
6. Deploy and monitor logs on Railway.

Required environment variables

- `TELEGRAM_BOT_TOKEN` (bot)
- `YOUTUBE_API_KEY` (app + bot)
- `OPENAI_API_KEY` (app + bot)
- `COMMENT_PROMPT_ID` (app)
- `TOPIC_ANALYSIS_PROMPT_ID` (app)

Tips

- The Dockerfiles avoid BuildKit-only features (such as `--mount=type=cache`) to ensure compatibility with Railway builders.
- Keep secrets in Railway environment variables and do not commit .env files.

If you want, I can also add Railway-specific `service` templates or CI steps. Let me know what you'd prefer.