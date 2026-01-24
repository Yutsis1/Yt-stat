import pytest
import httpx
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot import handlers
from app.i18n import t


@pytest.mark.asyncio
async def test_handle_youtube_link_timeout(monkeypatch):
    """If the analyze endpoint times out, the user gets a friendly timeout message."""
    # Mock settings
    mock_settings = SimpleNamespace(
        api_base_url="http://localhost:8000",
        http_max_retries=1,
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

    # Mock the AsyncClient to raise a timeout
    async def timeout_post(url, *args, **kwargs):
        raise httpx.ReadTimeout("timeout")

    mock_client = AsyncMock()
    mock_client.post = timeout_post
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

    # Ensure we replied with the timeout i18n message
    assert processing_msg.edit_text.await_count >= 1
    called_msg = processing_msg.edit_text.call_args_list[0].args[0]
    # Check for Russian or English timeout message
    assert "превышено время ожидания" in called_msg.lower() or "timeout" in called_msg.lower()


@pytest.mark.asyncio
async def test_post_with_retries_eventual_success(monkeypatch):
    """Verify _post_with_retries retries on ReadTimeout and eventually returns success."""
    call_state = {"n": 0}

    mock_response = SimpleNamespace(status_code=200, json=lambda: {"ok": True}, text='')

    async def fake_post(self, *args, **kwargs):
        if call_state["n"] < 2:
            call_state["n"] += 1
            raise httpx.ReadTimeout("timeout")
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

    client = httpx.AsyncClient()

    res = await handlers._post_with_retries(
        max_retries=3,
        timeout=1,
        backoff_base=0,
        backoff_max=1,
        client=client,
        url="http://example.local/test",
        json={"a": 1},
    )

    assert res is mock_response
    assert call_state["n"] == 2


@pytest.mark.asyncio
async def test_post_with_retries_missing_url_raises():
    """Ensure calling _post_with_retries without `url` raises a ValueError instead of TypeError."""
    import pytest

    client = None
    with pytest.raises(ValueError):
        await handlers._post_with_retries(
            max_retries=1,
            timeout=1,
            backoff_base=0,
            backoff_max=1,
            url=None
        )
