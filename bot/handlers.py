import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
import httpx
from bot.helpers.key_button import feedback_keyboard, language_keyboard, main_menu_keyboard
from bot.helpers.user_settings import get_user_language, set_user_language

from app.i18n import LANGUAGE_NAMES, get_language_name, t
from app.services.youtube import get_youtube_service
import asyncio

from config import get_settings

logger = logging.getLogger(__name__)

router = Router()


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

@router.callback_query(F.data.startswith("menu:"))
async def on_main_menu_action(callback: CallbackQuery):
    user_id = callback.from_user.id if callback.from_user else None
    language = get_user_language(user_id)

    if callback.message is None:
        await callback.answer()
        return

    action = callback.data.split(":", 1)[1]

    if action == "language":
        await callback.message.edit_text(
            t(language, "language_select"),
            reply_markup=language_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        await callback.answer()
        return

    if action == "help":
        await callback.message.edit_text(
            t(language, "help"),
            reply_markup=main_menu_keyboard(language),
            parse_mode=ParseMode.HTML,
        )
        await callback.answer()
        return

    await callback.answer()

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
    """Handle /start command."""
    user_id = message.from_user.id if message.from_user else None
    language = get_user_language(user_id)

    await message.answer(
        t(language, "welcome"),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(language),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    user_id = message.from_user.id if message.from_user else None
    language = get_user_language(user_id)

    await message.answer(
        t(language, "help"),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(language),
    )



@router.message(Command("language"))
async def cmd_language(message: Message):
    """Handle /language command."""
    from bot.helpers.user_settings import get_user_language
    language = get_user_language(
        message.from_user.id if message.from_user else None)
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
        set_user_language(user_id, selected_language)

    await callback.message.edit_text(
        t(selected_language, "language_set",
          language_name=get_language_name(selected_language)),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


async def _post_with_retries(
        max_retries: int,
        timeout: float,
        backoff_base: float,
        backoff_max: float,
        client: httpx.AsyncClient | None = None,
        url: str | None = None,
        **kwargs):
    """Post with retries for transient network errors and timeouts.

    Accepts an optional `client`. If no client is provided the helper will
    create a temporary `httpx.AsyncClient` for the duration of the call.
    """
    if url is None:
        raise ValueError("url is required for _post_with_retries")

    async def _do_post(client_obj: httpx.AsyncClient):
        for attempt in range(1, max_retries + 1):
            try:
                return await client_obj.post(url, timeout=timeout, **kwargs)
            except (httpx.ReadTimeout, httpx.RequestError) as exc:
                logger.warning(
                    "HTTP request failed (attempt %s/%s) for %s: %s", attempt, max_retries, url, exc)
                if attempt < max_retries:
                    sleep_for = min(
                        backoff_base * (2 ** (attempt - 1)), backoff_max)
                    await asyncio.sleep(sleep_for)
                    continue
                raise

    if client is None:
        async with httpx.AsyncClient() as _client:
            return await _do_post(_client)
    else:
        return await _do_post(client)


@router.message(F.text)
async def handle_youtube_link(message: Message):
    """Handle YouTube link messages."""
    text = message.text.strip()
    user_id = message.from_user.id if message.from_user else None
    language = get_user_language(user_id)


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
            settings = get_settings()
            # token = await get_bot_token()
            # headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                analyze_url = f"{settings.api_base_url}/analyze/youtube/comments"
                try:
                    r = await _post_with_retries(
                        client=client,
                        url=analyze_url,
                        json={"video_url": text, "language": language},
                        max_retries=settings.http_max_retries,
                        timeout=settings.http_timeout_s,
                        backoff_base=settings.http_backoff_base_s,
                        backoff_max=settings.http_backoff_max_s,
                    )
                except httpx.ReadTimeout as exc:
                    logger.error(
                        "Request timed out while contacting analyze endpoint %s: %s", analyze_url, exc)
                    await processing_msg.edit_text(
                        t(language, "request_timeout"),
                        parse_mode=ParseMode.HTML,
                    )
                    return
                except httpx.RequestError as exc:
                    logger.error(
                        "Network error while contacting analyze endpoint %s: %s", analyze_url, exc)
                    await processing_msg.edit_text(
                        t(language, "request_timeout"),
                        parse_mode=ParseMode.HTML,
                    )
                    return

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
        sentiments_text, likes_text = format_sentiment_and_likes(
            language, count_comments_per_sentiment, likes_per_category)
        feedback_url = (settings.feedback_form_url or "").strip()
        extra_lines: list[str] = [sentiments_text, likes_text]
        reply_markup = None
        if feedback_url:
            extra_lines.append(t(language, "feedback_cta"))
            reply_markup = feedback_keyboard(language, feedback_url)

        response = format_analysis_result(
            result,
            video_info.get("title", ""),
            language,
            *extra_lines,
        )
        await processing_msg.edit_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )

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
