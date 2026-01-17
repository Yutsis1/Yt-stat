import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
import httpx

from app.i18n import DEFAULT_LANGUAGE, LANGUAGE_NAMES, get_language_name, t
from app.services.youtube import get_youtube_service
from app.services.analyzer import get_analyzer
from bot.auth_client import ensure_authorized, get_bot_token, post_ingest
import asyncio

from config import get_settings

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


def format_sentiment_and_likes(language: str, sentiment_counts, likes_by_sentiment) -> tuple[str, str]:
    """Format sentiment counts and likes per sentiment into localized strings."""
    # Normalize inputs (accept Counter, dict or None)
    sentiment_counts = sentiment_counts or {}
    likes_by_sentiment = likes_by_sentiment or {}

    key_map = {
        "positive": "sentiment_positive",
        "negative": "sentiment_negative",
        "neutral": "sentiment_neutral",
        "nonsensical": "sentiment_nonsensical",
        "off-topic": "sentiment_off_topic",
    }

    # Comments by sentiment
    try:
        items = sorted(sentiment_counts.items(), key=lambda x: -x[1])
    except Exception:
        items = []
    lines1 = [t(language, "comments_by_sentiment_title")]
    for s, c in items:
        label_key = key_map.get(s, s)
        label = t(language, label_key)
        lines1.append(f"{label}: {c}")

    # Likes by sentiment
    try:
        items2 = sorted(likes_by_sentiment.items(), key=lambda x: -x[1])
    except Exception:
        items2 = []
    lines2 = [t(language, "likes_by_sentiment_title")]
    for s, c in items2:
        label_key = key_map.get(s, s)
        label = t(language, label_key)
        lines2.append(f"{label}: {c}")

    return ("\n".join(lines1), "\n".join(lines2))


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command: attempt to obtain an API token to authorize the bot."""
    language = get_user_language(message.from_user.id if message.from_user else None)

    # Attempt to get a token and report result
    if await ensure_authorized():
        await message.answer(
            t(language, "authorize_success"),
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer(
            t(language, "authorize_failed"),
            parse_mode=ParseMode.HTML,
        )

    # Also show the welcome message for convenience
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

    # Ensure the bot is authorized (we require a bot token to call protected endpoints)
    if not await ensure_authorized():
        await message.answer(
            t(language, "please_authorize"),
            parse_mode=ParseMode.HTML,
        )
        return

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
        # Call the internal analyze endpoint (uses YouTube service + analyzer internally)
        try:
            settings =  get_settings()
            token = await get_bot_token()
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{settings.api_base_url}/analyze/youtube/comments",
                    json={"video_url": text, "language": language},
                    headers=headers,
                    timeout=30.0,
                )

            if r.status_code == 403:
                await processing_msg.edit_text(
                    t(language, "cannot_access_comments", error=r.text),
                    parse_mode=ParseMode.HTML,
                )
                return
            if r.status_code == 404:
                await processing_msg.edit_text(
                    t(language, "video_not_found"),
                    parse_mode=ParseMode.HTML,
                )
                return
            if r.status_code == 400:
                body = r.json() if r.text else {}
                detail = body.get("detail", r.text)
                if "No comments" in str(detail):
                    await processing_msg.edit_text(
                        t(language, "no_comments"),
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await processing_msg.edit_text(
                        t(language, "error", error=detail),
                        parse_mode=ParseMode.HTML,
                    )
                return

            r.raise_for_status()
            data = r.json()
        except httpx.HTTPStatusError as e:
            await processing_msg.edit_text(
                t(language, "error", error=str(e)),
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception:
            logger.exception("Error analyzing video")
            await processing_msg.edit_text(
                t(language, "error_occurred"),
                parse_mode=ParseMode.HTML,
            )
            return

        video_info = data.get("video_info", {}) or {}
        video_line = f"<b>{t(language, 'video_label')}:</b> {video_info.get('title', '')}"
        channel_line = f"<b>{t(language, 'channel_label')}:</b> {video_info.get('channel', '')}"

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

        # Update progress
        count = data.get("comments_count", 0)
        await processing_msg.edit_text(
            t(
                language,
                "found_comments",
                video_line=video_line,
                channel_line=channel_line,
                count=count,
            ),
            parse_mode=ParseMode.HTML,
        )

        # Format and send result
        result = data.get("analyze_result", "")
        count_comments_per_sentiment = data.get("count_comments_per_sentiment")
        likes_per_category = data.get("likes_per_category")
        sentiments_text, likes_text = format_sentiment_and_likes(language, count_comments_per_sentiment, likes_per_category)
        response = format_analysis_result(
            result,
            video_info.get("title", ""),
            language,
            sentiments_text,
            likes_text,
        )
        await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)

        # Fire-and-forget ingest to the protected bot endpoint (non-blocking)
        try:
            asyncio.create_task(post_ingest({"video_id": video_info.get("video_id"), "summary": result}))
        except Exception:
            logger.exception("Failed to enqueue ingest task")

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
