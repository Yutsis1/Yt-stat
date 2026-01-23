from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.i18n import LANGUAGE_NAMES, t
from bot.helpers.callbacks import CB_LANGUAGE_EN, CB_LANGUAGE_RU, CB_MENU_HELP, CB_MENU_LANGUAGE


def main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    """
    Inline 'Main menu' keyboard reused by /start and /help.
    Labels are localized through i18n.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "menu_change_language"),
                    callback_data=CB_MENU_LANGUAGE,
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "menu_help"),
                    callback_data=CB_MENU_HELP,
                )
            ],
        ]
    )


def feedback_keyboard(language: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "feedback_button"),
                    url=url,
                )
            ]
        ]
    )

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LANGUAGE_NAMES["en"], callback_data=CB_LANGUAGE_EN),
                InlineKeyboardButton(
                    text=LANGUAGE_NAMES["ru"], callback_data=CB_LANGUAGE_RU),
            ]
        ]
    )