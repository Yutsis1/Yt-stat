from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from app.i18n import t
from callbacks import CB_MENU_HELP, CB_MENU_LANGUAGE

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