import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

from app.services.youtube import get_youtube_service
from app.services.analyzer import get_analyzer, CommentAnalyzer

logger = logging.getLogger(__name__)

router = Router()


def format_analysis_result(
        result: str, 
        video_title: str,
        *extra_lines: str
        ) -> str:
    """Format analysis result as a Telegram message."""
    
    
    lines = [
        f"📊 <b>Analysis Complete!</b>",
        f"",
        f"🎬 <b>Video:</b> {video_title}",
        f"💬 <b>Comments analyzed:</b> ",
        f"{result}",
        f"",
        f"",
    ]
    
    lines.extend(str(line) for line in extra_lines)
    
    return '\n'.join(lines)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "👋 <b>Welcome to YouTube Comment Analyzer!</b>\n\n"
        "Send me a YouTube video link and I'll analyze the comments to tell you:\n\n"
        "🏆 <b>Dominant comment type</b> - What kind of comments appear most\n"
        "👍 <b>Most liked comment type</b> - What kind of comments get the most likes\n\n"
        "Just paste a YouTube link to get started!",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "📖 <b>How to use this bot:</b>\n\n"
        "1. Copy a YouTube video URL\n"
        "2. Paste it here\n"
        "3. Wait for the analysis (usually 10-30 seconds)\n\n"
        "<b>Supported URL formats:</b>\n"
        "• https://youtube.com/watch?v=VIDEO_ID\n"
        "• https://youtu.be/VIDEO_ID\n"
        "• https://youtube.com/embed/VIDEO_ID\n\n"
        "<b>Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help message",
        parse_mode=ParseMode.HTML
    )


@router.message(F.text)
async def handle_youtube_link(message: Message):
    """Handle YouTube link messages."""
    text = message.text.strip()
    
    youtube_service = get_youtube_service()
    
    # Extract video ID
    video_id = youtube_service.extract_video_id(text)
    
    if not video_id:
        await message.answer(
            "❌ <b>Invalid YouTube link</b>\n\n"
            "Please send a valid YouTube video URL.\n"
            "Example: https://youtube.com/watch?v=dQw4w9WgXcQ",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Send processing message
    processing_msg = await message.answer(
        "⏳ <b>Analyzing video comments...</b>\n\n"
        "This may take 10-30 seconds depending on the number of comments.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        # Get video info
        video_info = youtube_service.get_video_info(video_id)
        if not video_info:
            await processing_msg.edit_text(
                "❌ <b>Video not found</b>\n\n"
                "The video might be private, deleted, or the link is incorrect.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Update message with video title
        await processing_msg.edit_text(
            f"⏳ <b>Analyzing comments...</b>\n\n"
            f"🎬 {video_info.title}\n"
            f"📺 {video_info.channel}\n\n"
            f"Fetching comments...",
            parse_mode=ParseMode.HTML
        )
        
        # Fetch comments
        comments = youtube_service.get_comments(video_id)
        
        if not comments:
            await processing_msg.edit_text(
                "❌ <b>No comments found</b>\n\n"
                "This video either has no comments or comments are disabled.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Update progress
        await processing_msg.edit_text(
            f"⏳ <b>Analyzing comments...</b>\n\n"
            f"🎬 {video_info.title}\n"
            f"📺 {video_info.channel}\n\n"
            f"Found {len(comments)} comments. Running AI analysis...",
            parse_mode=ParseMode.HTML
        )
        
        # Analyze comments
        analyzer = get_analyzer()
        result = await analyzer.analyze_async(comments)
        count_comments_per_sentiment = analyzer.count_comment_per_sentiment(comments)
        likes_per_category = analyzer.count_likes_per_category(comments)
        # Format and send result
        response = format_analysis_result(result, video_info.title, count_comments_per_sentiment, likes_per_category)
        await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
        
    except PermissionError as e:
        await processing_msg.edit_text(
            f"❌ <b>Cannot access comments</b>\n\n{str(e)}",
            parse_mode=ParseMode.HTML
        )
    except ValueError as e:
        await processing_msg.edit_text(
            f"❌ <b>Error</b>\n\n{str(e)}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.exception("Error analyzing video")
        await processing_msg.edit_text(
            "❌ <b>An error occurred</b>\n\n"
            "Please try again later. If the problem persists, the video might have "
            "too many comments or there might be an API issue.",
            parse_mode=ParseMode.HTML
        )
