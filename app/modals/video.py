from typing import Literal, Optional
from pydantic import BaseModel


class CommentAnalysisResult(BaseModel):
    """Holds analysis results for a comment."""
    sentiment: Literal["positive", "negative", "neutral", "nonsensical", "off-topic"]
    main_theme: str


class Comment(BaseModel):
    """Represents a YouTube comment."""
    text: str
    like_count: int
    author: str
    reply_count: int = 0
    analysis_result: Optional[CommentAnalysisResult] = None


class VideoInfo(BaseModel):
    """Basic video information."""
    video_id: str
    title: str
    channel: str

class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis."""
    video_url: str
    language: Optional[Literal["en", "ru"]] = "en"  # Default to English

class VideoAnalysisResponse(BaseModel):
    """Response model for video analysis."""
    analyze_result: str
    count_comments_per_sentiment: dict[str, int]
    likes_per_category: dict[str, int]