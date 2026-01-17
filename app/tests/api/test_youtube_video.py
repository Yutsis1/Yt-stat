from fastapi.testclient import TestClient
import pytest
from unittest.mock import Mock
from types import SimpleNamespace

from app.routers.analyze.youtube_video import app  # Import the specific router app
from app.tests.helpers.mock_library import YouTubeMock, OpenAIMock
from app.modals.video import Comment, VideoInfo, CommentAnalysisResult


client = TestClient(app)


@pytest.mark.asyncio
async def test_get_analyzis_for_comments(monkeypatch):
    """Test successful video comment analysis with mocked services."""
    # Setup YouTube mock
    youtube_mock = YouTubeMock()
    test_video_id = "dQw4w9WgXcQ"
    test_comments = [
        Comment(text="Great video!", like_count=10, author="User1", reply_count=2),
        Comment(text="This is terrible", like_count=1, author="User2", reply_count=0),
        Comment(text="Very informative content", like_count=5, author="User3", reply_count=1),
    ]
    youtube_mock.register_video(
        test_video_id,
        comments=test_comments,
        video_info=VideoInfo(video_id=test_video_id, title="Test Video", channel="Test Channel")
    )
    
    # Setup OpenAI mock
    openai_mock = OpenAIMock(default_output='{"sentiment":"neutral","main_theme":"general"}')
    openai_mock.register(
        test_comments[0].text,
        '{"sentiment":"positive","main_theme":"praise"}'
    )
    openai_mock.register(
        test_comments[1].text,
        '{"sentiment":"negative","main_theme":"criticism"}'
    )
    openai_mock.register(
        test_comments[2].text,
        '{"sentiment":"positive","main_theme":"informative"}'
    )
    # Register topic analysis response
    openai_mock.register(
        "analyze_topics",
        "Overall, viewers appreciate the content quality and find it informative."
    )
    
    # Setup analyzer mock
    from app.services.analyzer import CommentAnalyzer
    from config import get_settings
    
    settings = get_settings()
    analyzer = CommentAnalyzer()
    analyzer.openai_client.responses.create = openai_mock.create
    
    # Mock the service getters
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_youtube_service", lambda: youtube_mock)
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_analyzer", lambda: analyzer)
    
    # Mock authentication to bypass JWT validation
    def mock_auth_dependency():
        return SimpleNamespace(credentials="mock_token")
    
    from fastapi.security import HTTPBearer
    monkeypatch.setattr(
        "app.routers.analyze.youtube_video.HTTPBearer.__call__",
        lambda self, request: mock_auth_dependency()
    )
    
    # Make the request
    response = client.post("/analyze/youtube/comments", json={
        "video_url": f"https://www.youtube.com/watch?v={test_video_id}",
        "language": "en"
    })
    
    # Assertions
    assert response.status_code == 200
    
    data = response.json()
    assert "analyze_result" in data
    assert "count_comments_per_sentiment" in data
    assert "likes_per_category" in data
    assert "video_info" in data
    assert data.get("comments_count") == len(test_comments)
    
    # Verify sentiment distribution
    sentiment_counts = data["count_comments_per_sentiment"]
    assert sentiment_counts.get("positive", 0) == 2
    assert sentiment_counts.get("negative", 0) == 1
    
    # Verify likes per category
    likes = data["likes_per_category"]
    assert likes.get("positive", 0) == 15  # 10 + 5
    assert likes.get("negative", 0) == 1
    
    # Verify YouTube service was called correctly
    assert len(youtube_mock.calls) == 3
    assert youtube_mock.calls[0].method == "extract_video_id"
    assert test_video_id in youtube_mock.calls[0].args[0]
    assert youtube_mock.calls[1].method == "get_comments"
    assert youtube_mock.calls[2].method == "get_video_info"
    assert youtube_mock.calls[1].args[0] == test_video_id


@pytest.mark.asyncio
async def test_invalid_video_id(monkeypatch):
    """Test handling of invalid video ID."""
    youtube_mock = YouTubeMock()
    # Don't register any videos, so extract_video_id returns None
    
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_youtube_service", lambda: youtube_mock)
    
    # Mock authentication
    def mock_auth_dependency():
        return SimpleNamespace(credentials="mock_token")
    
    from fastapi.security import HTTPBearer
    monkeypatch.setattr(
        "app.routers.analyze.youtube_video.HTTPBearer.__call__",
        lambda self, request: mock_auth_dependency()
    )
    
    # Make request with invalid URL - should return 400 since id isn't registered
    response = client.post("/analyze/youtube/comments", json={
        "video_url": "https://www.youtube.com/watch?v=invalid",
        "language": "en"
    })
    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid video URL"

    # Verify extract_video_id was called
    assert len(youtube_mock.calls) > 0
    assert youtube_mock.calls[0].method == "extract_video_id"


@pytest.mark.asyncio
async def test_comments_disabled(monkeypatch):
    """Test handling when comments are disabled on a video."""
    youtube_mock = YouTubeMock()
    test_video_id = "disabledComments"
    
    # Register error for this video
    youtube_mock.register_error(test_video_id, PermissionError("Comments are disabled for this video"))
    
    from app.services.analyzer import CommentAnalyzer
    analyzer = CommentAnalyzer()
    
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_youtube_service", lambda: youtube_mock)
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_analyzer", lambda: analyzer)
    
    # Mock authentication
    def mock_auth_dependency():
        return SimpleNamespace(credentials="mock_token")
    
    from fastapi.security import HTTPBearer
    monkeypatch.setattr(
        "app.routers.analyze.youtube_video.HTTPBearer.__call__",
        lambda self, request: mock_auth_dependency()
    )
    
    # Make request - should return 403
    response = client.post("/analyze/youtube/comments", json={
        "video_url": f"https://www.youtube.com/watch?v={test_video_id}",
        "language": "en"
    })
    assert response.status_code == 403
    assert "Comments are disabled for this video" in response.json().get("detail", "")

    # Verify the methods were called
    assert len(youtube_mock.calls) >= 1
    get_comments_calls = [c for c in youtube_mock.calls if c.method == "get_comments"]
    assert len(get_comments_calls) == 1


@pytest.mark.asyncio
async def test_video_not_found(monkeypatch):
    """Test handling when video is not found."""
    youtube_mock = YouTubeMock()
    test_video_id = "notFoundVideo"
    
    # Register error for this video
    youtube_mock.register_error(test_video_id, ValueError("Video not found"))
    
    from app.services.analyzer import CommentAnalyzer
    analyzer = CommentAnalyzer()
    
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_youtube_service", lambda: youtube_mock)
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_analyzer", lambda: analyzer)
    
    # Mock authentication
    def mock_auth_dependency():
        return SimpleNamespace(credentials="mock_token")
    
    from fastapi.security import HTTPBearer
    monkeypatch.setattr(
        "app.routers.analyze.youtube_video.HTTPBearer.__call__",
        lambda self, request: mock_auth_dependency()
    )
    
    # Make request - should return 404
    response = client.post("/analyze/youtube/comments", json={
        "video_url": f"https://www.youtube.com/watch?v={test_video_id}",
        "language": "en"
    })
    assert response.status_code == 404
    assert response.json().get("detail") == "Video not found"

    # Verify the methods were called
    assert len(youtube_mock.calls) >= 1
    get_comments_calls = [c for c in youtube_mock.calls if c.method == "get_comments"]
    assert len(get_comments_calls) == 1


@pytest.mark.asyncio
async def test_empty_comments_list(monkeypatch):
    """Test handling when video has no comments."""
    youtube_mock = YouTubeMock()
    test_video_id = "noComments123"
    
    # Register video with empty comments list
    youtube_mock.register_video(
        test_video_id,
        comments=[],
        video_info=VideoInfo(video_id=test_video_id, title="No Comments Video", channel="Test Channel")
    )
    
    # Setup OpenAI mock with empty comment handling
    openai_mock = OpenAIMock(default_output="No comments to analyze.")
    
    from app.services.analyzer import CommentAnalyzer
    analyzer = CommentAnalyzer()
    analyzer.openai_client.responses.create = openai_mock.create
    
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_youtube_service", lambda: youtube_mock)
    monkeypatch.setattr("app.routers.analyze.youtube_video.get_analyzer", lambda: analyzer)
    
    # Mock authentication
    def mock_auth_dependency():
        return SimpleNamespace(credentials="mock_token")
    
    from fastapi.security import HTTPBearer
    monkeypatch.setattr(
        "app.routers.analyze.youtube_video.HTTPBearer.__call__",
        lambda self, request: mock_auth_dependency()
    )
    
    # Make request - should return 400 for empty comments
    response = client.post("/analyze/youtube/comments", json={
        "video_url": f"https://www.youtube.com/watch?v={test_video_id}",
        "language": "en"
    })
    assert response.status_code == 400
    assert response.json().get("detail") == "No comments to analyze"

    # Verify YouTube service was called correctly
    assert len(youtube_mock.calls) == 2
    assert youtube_mock.calls[0].method == "extract_video_id"
    assert youtube_mock.calls[1].method == "get_comments" 