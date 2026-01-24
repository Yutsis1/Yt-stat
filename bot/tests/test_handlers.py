import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, MagicMock, patch

from bot import handlers
from app.modals import Comment, VideoInfo


@pytest.mark.asyncio
async def test_handle_youtube_link_uses_analyzer(monkeypatch):
    """Test that tg interface is working."""
    comments = [
        Comment(text="Nice!", like_count=2, author="A"),
        Comment(text="Not great", like_count=0, author="B"),
    ]

    # Mock settings
    mock_settings = SimpleNamespace(
        api_base_url="http://localhost:8000",
        http_max_retries=3,
        http_timeout_s=30,
        http_backoff_base_s=0.1,
        http_backoff_max_s=5,
        feedback_form_url="",
    )
    monkeypatch.setattr("bot.handlers.get_settings", lambda: mock_settings)

    # Mock YouTube service
    mock_youtube_service = SimpleNamespace(
        extract_video_id=lambda url: "video123"
    )
    monkeypatch.setattr("bot.handlers.get_youtube_service", lambda: mock_youtube_service)

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
        raise_for_status=lambda: None,  # Add this method
    )

    # Mock the AsyncClient
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

    processing_msg = SimpleNamespace(edit_text=AsyncMock())
    message = SimpleNamespace(
        text="https://youtu.be/video123",
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(return_value=processing_msg),
    )

    await handlers.handle_youtube_link(message)

    assert processing_msg.edit_text.await_count >= 1
    final_message = processing_msg.edit_text.call_args_list[-1].args[0]
    assert "Summary text" in final_message
    assert "Test Video" in final_message


@pytest.mark.asyncio
async def test_invalid_youtube_link(monkeypatch):
    """Test that invalid YouTube link shows error message."""
    # Mock YouTube service
    mock_youtube_service = SimpleNamespace(
        extract_video_id=lambda url: None
    )
    monkeypatch.setattr("bot.handlers.get_youtube_service", lambda: mock_youtube_service)

    message = SimpleNamespace(
        text="not-a-youtube-link",
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(),
    )

    await handlers.handle_youtube_link(message)

    message.answer.assert_awaited_once()
    called_msg = message.answer.call_args.args[0]
    # Message is in Russian by default, so check for either Russian or English
    assert "invalid" in called_msg.lower() or "некорректна" in called_msg.lower()
