import time
import secrets
from typing import Optional, Dict, Any

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.modals.auth import TokenRequest, TokenResponse
from app.modals.video import VideoAnalysisRequest, VideoAnalysisResponse
from app.services.analyzer import get_analyzer
from app.services.youtube import get_youtube_service
from config import get_settings

settings = get_settings()

app = FastAPI()
youtube_router = APIRouter(
    prefix="/analyze/youtube",
    tags=["YouTube Analysis"],
)


@youtube_router.post("/comments", response_model=VideoAnalysisResponse)
async def analyze_youtube_video(
    request: VideoAnalysisRequest,
    creds: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
) -> VideoAnalysisResponse:
    youtube_service = get_youtube_service()
    video_id = youtube_service.extract_video_id(request.video_url)
    comments = youtube_service.get_comments(video_id)
    analyzer = get_analyzer()
    result = await analyzer.analyze_async(comments, language=request.language)
    count_comments_per_sentiment = analyzer.count_comment_per_sentiment(comments)
    likes_per_category = analyzer.count_likes_per_category(comments)

    
    return VideoAnalysisResponse(
        analyze_result=result,
        count_comments_per_sentiment=dict(count_comments_per_sentiment),
        likes_per_category=dict(likes_per_category),
    )

app.include_router(youtube_router)