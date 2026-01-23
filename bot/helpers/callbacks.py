from app.i18n import t
from bot.handlers import get_user_language
from bot.helpers.key_button import language_keyboard, main_menu_keyboard
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

router = Router()

CB_MENU_LANGUAGE = "menu:language"
CB_MENU_HELP = "menu:help"
CB_LANGUAGE_EN = "lang:en"
CB_LANGUAGE_RU = "lang:ru"

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
