import re
import random
from typing import Literal
from dataclasses import dataclass
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import get_settings
from app.modals import Comment, VideoInfo



class YouTubeService:
    """Service for interacting with YouTube Data API."""
    
    # Patterns to extract video ID from various YouTube URL formats
    VIDEO_ID_PATTERNS = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
    ]
    
    def __init__(self):
        settings = get_settings()
        self.youtube = build('youtube', 'v3', developerKey=settings.youtube_api_key)
        self.max_comments = settings.max_comments
    
    def extract_video_id(self, url_or_id: str) -> str | None:
        """Extract video ID from a YouTube URL or return the ID if already valid."""
        url_or_id = url_or_id.strip()
        
        for pattern in self.VIDEO_ID_PATTERNS:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    def get_video_info(self, video_id: str) -> VideoInfo | None:
        """Fetch basic video information."""
        try:
            response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
            
            snippet = response['items'][0]['snippet']
            return VideoInfo(
                video_id=video_id,
                title=snippet.get('title', 'Unknown'),
                channel=snippet.get('channelTitle', 'Unknown')
            )
        except HttpError:
            return None
    
    def get_comments(self, 
                    video_id: str,
                    comment_chunk_size: int = None,
                    order: Literal['time', 'relevance'] = 'relevance',
                    # mode: Literal['random', 'top'] = 'random'
                    ) -> list[Comment]:
        """
        Fetch top comments for a video sorted by relevance or time.
        pram video_id: YouTube video ID
        param comment_chunk_size: Number of comments to fetch (default: max_comments from settings)
        param order: Order of comments, either 'time' or 'relevance' (default: 'relevance')
        """
        comments = []
        if comment_chunk_size is None:
            comment_chunk_size = self.max_comments
        try:
            # Fetch top-level comments sorted by relevance
            response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                order=order,
                maxResults=comment_chunk_size,
                textFormat='plainText'
            ).execute()
            
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comments.append(Comment(
                    text=snippet.get('textDisplay', ''),
                    like_count=snippet.get('likeCount', 0),
                    author=snippet.get('authorDisplayName', 'Anonymous'),
                    reply_count=item['snippet'].get('totalReplyCount', 0)
                ))
            
            # Fetch more if needed and available
            # Commenred out for now to limit to single chunk for beta launch
            # next_page_token = response.get('nextPageToken')
            # while next_page_token and len(comments) < self.max_comments:
            #     response = self.youtube.commentThreads().list(
            #         part='snippet',
            #         videoId=video_id,
            #         order='relevance',
            #         maxResults=min(self.max_comments - len(comments), 100),
            #         pageToken=next_page_token,
            #         textFormat='plainText'
            #     ).execute()
                
            #     for item in response.get('items', []):
            #         snippet = item['snippet']['topLevelComment']['snippet']
            #         comments.append(Comment(
            #             text=snippet.get('textDisplay', ''),
            #             like_count=snippet.get('likeCount', 0),
            #             author=snippet.get('authorDisplayName', 'Anonymous'),
            #             reply_count=item['snippet'].get('totalReplyCount', 0)
            #         ))
                
            #     next_page_token = response.get('nextPageToken')
        
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError("Comments are disabled for this video")
            elif e.resp.status == 404:
                raise ValueError("Video not found")
            raise
        
        return comments



# Singleton instance
_youtube_service: YouTubeService | None = None


def get_youtube_service() -> YouTubeService:
    """Get or create YouTube service singleton."""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
