from fastapi import FastAPI, APIRouter, HTTPException, status
from app.modals.video import VideoAnalysisRequest, VideoAnalysisResponse, VideoInfo
from app.services.analyzer import get_analyzer
from app.services.youtube import get_youtube_service

app = FastAPI()
youtube_router = APIRouter(
    prefix="/analyze/youtube",
    tags=["YouTube Analysis"],
)


@youtube_router.post("/comments", response_model=VideoAnalysisResponse)
async def analyze_youtube_video(
    request: VideoAnalysisRequest,
) -> VideoAnalysisResponse:
    youtube_service = get_youtube_service()
    video_id = youtube_service.extract_video_id(request.video_url)
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid video URL")

    try:
        comments = youtube_service.get_comments(video_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not comments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No comments to analyze")

    try:
        video_info = youtube_service.get_video_info(video_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not video_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    analyzer = get_analyzer()
    result = await analyzer.analyze_async(comments, language=request.language)
    count_comments_per_sentiment = analyzer.count_comment_per_sentiment(comments)
    likes_per_category = analyzer.count_likes_per_category(comments)

    return VideoAnalysisResponse(
        analyze_result=result,
        count_comments_per_sentiment=dict(count_comments_per_sentiment),
        likes_per_category=dict(likes_per_category),
        video_info=video_info,
        comments_count=len(comments),
    )

app.include_router(youtube_router)
