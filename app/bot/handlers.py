import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

from app.i18n import DEFAULT_LANGUAGE, LANGUAGE_NAMES, get_language_name, t
from app.services.youtube import get_youtube_service
from app.services.analyzer import get_analyzer

logger = logging.getLogger(__name__)

router = Router()
_user_languages: dict[int, str] = {}


def get_user_language(user_id: int | None) -> str:
    if user_id is None:
        return DEFAULT_LANGUAGE
    return _user_languages.get(user_id, DEFAULT_LANGUAGE)


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LANGUAGE_NAMES["en"], callback_data="lang:en"),
                InlineKeyboardButton(text=LANGUAGE_NAMES["ru"], callback_data="lang:ru"),
            ]
        ]
    )


def format_analysis_result(
    result: str,
    video_title: str,
    language: str,
    *extra_lines: str,
) -> str:
    """Format analysis result as a Telegram message."""

    lines = [
        f"<b>{t(language, 'analysis_complete')}</b>",
        "",
        f"<b>{t(language, 'video_label')}:</b> {video_title}",
        f"<b>{t(language, 'comments_analyzed')}:</b>",
        f"{result}",
        "",
        "",
    ]

    lines.extend(str(line) for line in extra_lines)

    return "\n".join(lines)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    language = get_user_language(message.from_user.id if message.from_user else None)
    await message.answer(
        t(language, "welcome"),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    language = get_user_language(message.from_user.id if message.from_user else None)
    await message.answer(
        t(language, "help"),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("language"))
async def cmd_language(message: Message):
    """Handle /language command."""
    language = get_user_language(message.from_user.id if message.from_user else None)
    await message.answer(
        t(language, "language_select"),
        reply_markup=language_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    """Handle language selection callbacks."""
    user_id = callback.from_user.id if callback.from_user else None
    selected_language = callback.data.split(":", 1)[1]
    if selected_language not in LANGUAGE_NAMES:
        await callback.answer()
        return
    if callback.message is None:
        await callback.answer()
        return

    if user_id is not None:
        _user_languages[user_id] = selected_language

    await callback.message.edit_text(
        t(selected_language, "language_set", language_name=get_language_name(selected_language)),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.message(F.text)
async def handle_youtube_link(message: Message):
    """Handle YouTube link messages."""
    text = message.text.strip()
    language = get_user_language(message.from_user.id if message.from_user else None)

    youtube_service = get_youtube_service()

    # Extract video ID
    video_id = youtube_service.extract_video_id(text)

    if not video_id:
        await message.answer(
            t(language, "invalid_link"),
            parse_mode=ParseMode.HTML,
        )
        return

    # Send processing message
    processing_msg = await message.answer(
        t(language, "processing"),
        parse_mode=ParseMode.HTML,
    )

    try:
        # Get video info
        video_info = youtube_service.get_video_info(video_id)
        if not video_info:
            await processing_msg.edit_text(
                t(language, "video_not_found"),
                parse_mode=ParseMode.HTML,
            )
            return

        video_line = f"<b>{t(language, 'video_label')}:</b> {video_info.title}"
        channel_line = f"<b>{t(language, 'channel_label')}:</b> {video_info.channel}"

        # Update message with video title
        await processing_msg.edit_text(
            t(
                language,
                "analyzing_comments",
                video_line=video_line,
                channel_line=channel_line,
            ),
            parse_mode=ParseMode.HTML,
        )

        # Fetch comments
        comments = youtube_service.get_comments(video_id)

        if not comments:
            await processing_msg.edit_text(
                t(language, "no_comments"),
                parse_mode=ParseMode.HTML,
            )
            return

        # Update progress
        await processing_msg.edit_text(
            t(
                language,
                "found_comments",
                video_line=video_line,
                channel_line=channel_line,
                count=len(comments),
            ),
            parse_mode=ParseMode.HTML,
        )

        # Analyze comments
        analyzer = get_analyzer()
        result = await analyzer.analyze_async(comments, language=language)
        count_comments_per_sentiment = analyzer.count_comment_per_sentiment(comments)
        likes_per_category = analyzer.count_likes_per_category(comments)
        # Format and send result
        response = format_analysis_result(
            result,
            video_info.title,
            language,
            count_comments_per_sentiment,
            likes_per_category,
        )
        await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)

    except PermissionError as e:
        await processing_msg.edit_text(
            t(language, "cannot_access_comments", error=str(e)),
            parse_mode=ParseMode.HTML,
        )
    except ValueError as e:
        await processing_msg.edit_text(
            t(language, "error", error=str(e)),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        logger.exception("Error analyzing video")
        await processing_msg.edit_text(
            t(language, "error_occurred"),
            parse_mode=ParseMode.HTML,
        )
