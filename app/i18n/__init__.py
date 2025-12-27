import app.i18n.en as en
import app.i18n.ru as ru

DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Русский",
}

STRINGS = {}
STRINGS.update(en.STRINGS_EN)
STRINGS.update(ru.STRINGS_RU)
def get_language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES[DEFAULT_LANGUAGE])


def t(language: str, key: str, **kwargs) -> str:
    selected_language = language if language in STRINGS else DEFAULT_LANGUAGE
    template = STRINGS.get(selected_language, {}).get(key) or STRINGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
