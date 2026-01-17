# Copilot / AI Agent Instructions for Yt-stat

Summary
- This repo is a small FastAPI + aiogram Telegram bot that analyzes YouTube comments using OpenAI.
- Key flows: Telegram message -> `app.bot.handlers` -> `app.services.youtube` fetches comments -> `app.services.analyzer` calls OpenAI Responses API to categorize comments and produce a topic summary.

Quick start (developer)
- Create and activate a venv, install deps: `pip install -r requirements.txt` (Python 3.14+)
- Provide env vars (or copy `.env.example` to `.env` and edit):
  - `TELEGRAM_BOT_TOKEN`, `YOUTUBE_API_KEY`, `OPENAI_API_KEY`
  - `COMMENT_PROMPT_ID`, `TOPIC_ANALYSIS_PROMPT_ID` (used to select stored prompts in OpenAI responses)
  - If you update `config.py`, also update `.env.example` and any tests that rely on those settings (tests should call `get_settings.cache_clear()` to  pick up changes).
- Run locally (polling/dev): `python run_polling.py`
- Run (production-like): `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Tests: `pytest` (project includes pytest and pytest-asyncio)
- Debugging: When running or debugging from your editor/IDE, make sure to use the project's .venv Python interpreter for execution (activate the virtualenv with `source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\activate` on Windows), or configure your debugger to use the `.venv` python executable.

Architecture & important files
- `app/main.py` — FastAPI app and lifecycle; will run bot as either polling (dev) or (production). Use `run_polling.py` for local testing.
- `bot/handlers.py` — Telegram handlers and message flow. Key responsibilities:
  - Validate / extract YouTube ID
  - Use `get_youtube_service()` for video/comments
  - Use `get_analyzer()` to run OpenAI analysis
  - Send/edit messages using HTML `ParseMode` (handlers use `ParseMode.HTML`) — keep returned text HTML-safe.
- `app/services/youtube.py` — YouTube API access (singleton via `get_youtube_service()`).
  - `extract_video_id()` supports URLs and raw IDs
  - `get_comments()` returns a list of `Comment` objects; raises `PermissionError` when comments disabled and `ValueError` when video not found
- `app/services/analyzer.py` — Async OpenAI usage and retry/backoff logic.
  - Uses `openai.AsyncOpenAI` (`openai.responses.create`) with `model`, `input`, `prompt` and expects `output_text` on the response
  - Concurrency knobs: `MAX_IN_FLIGHT_REQUESTS`, `BATCH_SIZE`, `MAX_RETRIES`, `BASE_BACKOFF_S` — tune for rate limiting
  - Skips comments that contain links (see `contains_link()`) to avoid spam/irrelevant items
- `app/modals/__init__.py` — Domain dataclasses: `Comment`, `ComentAnalysisResult`,  `VideoInfo` — tests rely on these shapes.
- `app/i18n/*` — Localization strings; `t(language, key, ...)` helper is used to format messages.

Testing & common test patterns
- Tests set env vars and call `get_settings.cache_clear()` to ensure `Settings` picks up test env variables (see `tests/test_analyzer.py` fixture `settings_env`).
- OpenAI is stubbed with `app.tests.mock_library.OpenAIMock`:
  - Register input-to-output mappings with `register(input_text, output_text)`
  - Assign `analyzer.openai_client.responses.create = openai_mock.create` in tests to intercept calls
  - `OpenAIMock` stores calls for assertion (`openai_mock.calls`)
- Services are commonly swapped in tests via monkeypatch/setattr; e.g.:
  - `monkeypatch.setattr('app.bot.handlers.get_youtube_service', lambda: youtube_service)`
  - `monkeypatch.setattr('app.bot.handlers.get_analyzer', lambda: analyzer)`
- Handler tests use simple namespace objects with `AsyncMock` for message operations (see `tests/test_handlers.py`)

Behavioral quirks & gotchas (do not change without understanding)
- The `ComentAnalysisResult` type name contains a typo; tests and code expect this name — do not rename without updating tests.
- Handlers expect `message.answer()` to return an object with `edit_text()` (they use a single message instance that gets edited many times). Tests emulate this with a `processing_msg` object.
- Analyzer uses `responses.create(model=..., input=..., prompt=...)` and parses `resp.output_text` as JSON (for single comment analysis). Follow that contract when making changes.
- `youtube.get_comments()` currently fetches a single page (comment pagination is intentionally commented out) — behavior and limits are by design until expanded.


Every time when creates `app.services` need to add its own test mock under `app.tests.mock_library`.
How to extend or mock OpenAI behavior
- Test helpers: prefer `OpenAIMock` to mimic real responses and capture calls.
- Production code uses `COMMENT_PROMPT_ID` and `TOPIC_ANALYSIS_PROMPT_ID` from settings — provide proper Prompt IDs or values in your environment when integrating with OpenAI.

Contribution tips
- Keep the async + sync boundary in mind. Analyzer provides both async (`analyze_async`) and a sync wrapper (`categorize_comments`) which uses `asyncio.run`.
- When adding features that change message text, update i18n entries under `app/i18n/` and add tests asserting final message content (see `tests/test_handlers.py`).

- make sure that `.github/copilot-instructions.md` and `.codex/agents.md` has same content inside


If anything here is unclear or you want more examples (e.g., a stub for testing another OpenAI pattern or an example of adding a new i18n string), tell me which area you'd like expanded and I will update this file. Thanks! ✅
