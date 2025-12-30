from typing_extensions import Literal
from attr import dataclass


@dataclass
class Comment:
    """Represents a YouTube comment."""
    text: str
    like_count: int
    author: str
    reply_count: int = 0
    analysis_result: "CommentAnalysisResult" = None

@dataclass
class CommentAnalysisResult:
    """Holds analysis results for a comment."""
    sentiment: Literal["positive", "negative", "neutral", "nonsensical", "off-topic"]
    main_theme: str

@dataclass
class VideoInfo:
    """Basic video information."""
    video_id: str
    title: str
    channel: str
