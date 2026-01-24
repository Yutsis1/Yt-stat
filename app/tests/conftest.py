import pytest

from config import get_settings


@pytest.fixture(autouse=True)
def settings_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-youtube")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("COMMENT_PROMPT_ID", "comment-prompt")
    monkeypatch.setenv("TOPIC_ANALYSIS_PROMPT_ID", "topic-prompt")
    monkeypatch.setenv("BOT_CLIENT_ID", "test-bot-client-id")
    monkeypatch.setenv("BOT_CLIENT_SECRET", "test-bot-client-secret")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()