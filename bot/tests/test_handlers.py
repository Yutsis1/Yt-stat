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

    youtube_service = SimpleNamespace(
        extract_video_id=Mock(return_value="video123"),
        get_video_info=Mock(return_value=VideoInfo(video_id="video123", title="Test Video", channel="Test Ch")),
        get_comments=Mock(return_value=comments),
    )

    # Ensure handler thinks the bot is authorized and avoid scheduling background tasks in tests
    monkeypatch.setattr(handlers, 'ensure_authorized', AsyncMock(return_value=True))
    monkeypatch.setattr(handlers, 'post_ingest', AsyncMock(return_value={}))
    monkeypatch.setattr(handlers.asyncio, 'create_task', lambda c: None)

    analyzer = SimpleNamespace(
        analyze_async=AsyncMock(return_value="Summary text"),
        count_comment_per_sentiment=Mock(return_value={"positive": 1, "negative": 1}),
        count_likes_per_category=Mock(return_value={"positive": 2, "negative": 0}),
    )

    processing_msg = SimpleNamespace(edit_text=AsyncMock())
    message = SimpleNamespace(
        text="https://youtu.be/video123",
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(return_value=processing_msg),
    )

    monkeypatch.setattr("app.bot.handlers.get_youtube_service", lambda: youtube_service)
    monkeypatch.setattr("app.bot.handlers.get_analyzer", lambda: analyzer)
    await handlers.handle_youtube_link(message)

    analyzer.analyze_async.assert_awaited_once_with(comments, language="en")
    analyzer.count_comment_per_sentiment.assert_called_once_with(comments)
    analyzer.count_likes_per_category.assert_called_once_with(comments)

    assert processing_msg.edit_text.await_count >= 3
    final_message = processing_msg.edit_text.call_args_list[-1].args[0]
    assert "Summary text" in final_message
    assert "Test Video" in final_message
    assert "Comments by sentiment" in final_message

    youtube_service.extract_video_id.assert_called_once_with("https://youtu.be/video123")
    youtube_service.get_video_info.assert_called_once_with("video123")
    youtube_service.get_comments.assert_called_once_with("video123")


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
