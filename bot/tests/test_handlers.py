import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from bot import handlers
from app.modals import Comment, VideoInfo


@pytest.mark.asyncio
async def test_handle_youtube_link_uses_analyzer(monkeypatch):
    """Test that tg interface is working."""
    handlers._user_languages.clear()
    comments = [
        Comment(text="Nice!", like_count=2, author="A"),
        Comment(text="Not great", like_count=0, author="B"),
    ]

    # Ensure handler thinks the bot is authorized and avoid scheduling background tasks in tests
    monkeypatch.setattr(handlers, 'ensure_authorized', AsyncMock(return_value=True))
    monkeypatch.setattr(handlers, 'post_ingest', AsyncMock(return_value={}))
    monkeypatch.setattr(handlers.asyncio, 'create_task', lambda c: None)
    monkeypatch.setattr('bot.handlers.get_bot_token', AsyncMock(return_value='mocktoken'))

    # Prepare mock HTTP response from analyze endpoint
    mock_response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "analyze_result": "Summary text",
            "count_comments_per_sentiment": {"positive": 1, "negative": 1},
            "likes_per_category": {"positive": 2, "negative": 0},
            "video_info": {"video_id": "video123", "title": "Test Video", "channel": "Test Ch"},
            "comments_count": len(comments),
        },
        text='',
    )

    async def fake_post(self, *args, **kwargs):
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

    processing_msg = SimpleNamespace(edit_text=AsyncMock())
    message = SimpleNamespace(
        text="https://youtu.be/video123",
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(return_value=processing_msg),
    )

    await handlers.handle_youtube_link(message)

    assert processing_msg.edit_text.await_count >= 2
    final_message = processing_msg.edit_text.call_args_list[-1].args[0]
    assert "Summary text" in final_message
    assert "Test Video" in final_message
    assert "Comments by sentiment" in final_message


@pytest.mark.asyncio
async def test_requires_authorization_shows_message(monkeypatch):
    handlers._user_languages.clear()
    message = SimpleNamespace(
        text="https://youtu.be/video123",
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(),
    )

    # Simulate unauthorized state
    monkeypatch.setattr(handlers, 'ensure_authorized', AsyncMock(return_value=False))

    await handlers.handle_youtube_link(message)

    message.answer.assert_awaited_once()
    called_msg = message.answer.call_args.args[0]
    assert "authorize" in called_msg.lower() or "/start" in called_msg.lower()
