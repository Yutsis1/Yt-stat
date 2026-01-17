import pytest
import httpx
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot import handlers
from app.i18n import t


@pytest.mark.asyncio
async def test_handle_youtube_link_timeout(monkeypatch):
    """If the analyze endpoint times out, the user gets a friendly timeout message."""
    handlers._user_languages.clear()
    handlers._authorized_users.clear()

    async def fake_post(self, *args, **kwargs):
        raise httpx.ReadTimeout("timeout")

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

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
    assert t('en', 'request_timeout') in called_msg


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
        client,
        "http://example.local/test",
        max_retries=3,
        timeout=1,
        backoff_base=0,
        backoff_max=1,
        json={"a": 1},
    )

    assert res is mock_response
    assert call_state["n"] == 2


async def test_post_with_retries_missing_url_raises():
    """Ensure calling _post_with_retries without `url` raises a ValueError instead of TypeError."""
    import pytest

    client = None
    with pytest.raises(ValueError):
        await handlers._post_with_retries(client, None, max_retries=1, timeout=1, backoff_base=0, backoff_max=1)
