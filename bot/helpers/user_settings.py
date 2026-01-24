# Better to move that in DB in future
# but for MVP this will do

from app.i18n import DEFAULT_LANGUAGE

_user_languages: dict[int, str] = {}

def get_user_language(user_id: int | None) -> str:
    if user_id is None:
        return DEFAULT_LANGUAGE
    return _user_languages.get(user_id, DEFAULT_LANGUAGE)

def set_user_language(user_id: int, language: str) -> None:
    """Set the language preference for a user."""
    _user_languages[user_id] = language