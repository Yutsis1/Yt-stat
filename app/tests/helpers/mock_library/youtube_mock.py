from dataclasses import dataclass
from typing import Any
from app.modals.video import Comment, VideoInfo


@dataclass
class YouTubeCall:
    """Record of a YouTube service method call."""
    method: str
    args: tuple
    kwargs: dict


class YouTubeMock:
    """Mock YouTube service for testing. Register video ID -> data mappings."""

    def __init__(self):
        self.video_data: dict[str, dict[str, Any]] = {}
        self.video_errors: dict[str, Exception] = {}
        self.calls: list[YouTubeCall] = []

    def register_video(
        self,
        video_id: str,
        *,
        comments: list[Comment] | None = None,
        video_info: VideoInfo | None = None,
    ) -> None:
        """Register mock data for a video ID."""
        self.video_data[video_id] = {
            "comments": comments or [],
            "video_info": video_info,
        }

    def register_error(self, video_id: str, error: Exception) -> None:
        """Register an error to raise for a video ID."""
        self.video_errors[video_id] = error

    def extract_video_id(self, url_or_id: str) -> str | None:
        """Mock extract_video_id - returns the ID if registered, else None."""
        self.calls.append(YouTubeCall(
            method="extract_video_id",
            args=(url_or_id,),
            kwargs={}
        ))
        
        url_or_id = url_or_id.strip()
        
        # Try to extract from common URL patterns first
        patterns = [
            (r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)", 1),
            (r"youtu\.be/([a-zA-Z0-9_-]+)", 1),
            (r"youtube\.com/embed/([a-zA-Z0-9_-]+)", 1),
            (r"youtube\.com/v/([a-zA-Z0-9_-]+)", 1),
        ]
        
        import re
        for pattern, group in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                video_id = match.group(group)
                # Check if this video ID is registered or has an error registered
                if video_id in self.video_data or video_id in self.video_errors:
                    return video_id
        
        # Check if it's a direct video ID match
        if url_or_id in self.video_data or url_or_id in self.video_errors:
            return url_or_id
        
        return None

    def get_video_info(self, video_id: str) -> VideoInfo | None:
        """Mock get_video_info - returns registered VideoInfo or None."""
        self.calls.append(YouTubeCall(
            method="get_video_info",
            args=(video_id,),
            kwargs={}
        ))
        
        if video_id in self.video_errors:
            raise self.video_errors[video_id]
        
        if video_id in self.video_data:
            return self.video_data[video_id]["video_info"]
        
        return None

    def get_comments(
        self,
        video_id: str,
        comment_chunk_size: int | None = None,
        order: str = 'relevance',
    ) -> list[Comment]:
        """Mock get_comments - returns registered comments or raises error."""
        self.calls.append(YouTubeCall(
            method="get_comments",
            args=(video_id,),
            kwargs={
                "comment_chunk_size": comment_chunk_size,
                "order": order,
            }
        ))
        
        if video_id in self.video_errors:
            raise self.video_errors[video_id]
        
        if video_id in self.video_data:
            return self.video_data[video_id]["comments"]
        
        raise ValueError("Video not found")
