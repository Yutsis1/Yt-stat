import pytest

from config import get_settings
from app.modals.video import Comment
from app.services.analyzer import CommentAnalyzer
from app.tests.helpers.mock_library import OpenAIMock


# @pytest.fixture(autouse=True)
# def settings_env(monkeypatch):
#     monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
#     monkeypatch.setenv("YOUTUBE_API_KEY", "test-youtube")
#     monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
#     monkeypatch.setenv("COMMENT_PROMPT_ID", "comment-prompt")
#     monkeypatch.setenv("TOPIC_ANALYSIS_PROMPT_ID", "topic-prompt")
#     get_settings.cache_clear()
#     yield
#     get_settings.cache_clear()


@pytest.mark.asyncio
async def test_analyze_async_uses_openai_api_responses():
    analyzer = CommentAnalyzer()
    openai_mock = OpenAIMock(default_output="Overall summary")
    openai_mock.register(
        "Great video!",
        '{"sentiment":"positive","main_theme":"praise"}',
    )
    openai_mock.register(
        "I hate this",
        '{"sentiment":"negative","main_theme":"complaint"}',
    )

    analyzer.openai_client.responses.create = openai_mock.create

    comments = [
        Comment(text="Great video!", like_count=3, author="A"),
        Comment(text="I hate this", like_count=1, author="B"),
    ]

    result = await analyzer.analyze_async(comments, language="en")

    assert result == "Overall summary"
    assert comments[0].analysis_result.sentiment == "positive"
    assert comments[1].analysis_result.sentiment == "negative"

    prompt_ids = {call.prompt.get("id") for call in openai_mock.calls}
    assert "comment-prompt" in prompt_ids
    assert "topic-prompt" in prompt_ids
    assert len(openai_mock.calls) == 3

    expected_topic_input = str(
        [
            {
                "main_theme": "praise",
                "like_count": 3,
                "sentiment": "positive",
            },
            {
                "main_theme": "complaint",
                "like_count": 1,
                "sentiment": "negative",
            },
        ]
    )
    inputs = {str(call.input) for call in openai_mock.calls}
    assert expected_topic_input in inputs
