DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Русский",
}

STRINGS = {
    "en": {
        "analysis_complete": "Analysis Complete!",
        "video_label": "Video",
        "channel_label": "Channel",
        "comments_analyzed": "Comments analyzed",
        "welcome": (
            "<b>Welcome to YouTube Comment Analyzer!</b>\n\n"
            "Send me a YouTube video link and I'll analyze the comments to tell you:\n\n"
            "<b>Dominant comment type</b> - What kind of comments appear most\n"
            "<b>Most liked comment type</b> - What kind of comments get the most likes\n\n"
            "Paste the link for your video here and you will get summary for 30 random comments."
        ),
        "help": (
            "<b>How to use this bot:</b>\n\n"
            "1. Copy a YouTube video URL\n"
            "2. Paste it here\n"
            "3. Wait for the analysis (usually 10-30 seconds)\n\n"
            "Paste the link for your video here and you will get summary for 30 random comments.\n\n"
            "<b>Supported URL formats:</b>\n"
            "- https://youtube.com/watch?v=VIDEO_ID\n"
            "- https://youtu.be/VIDEO_ID\n"
            "- https://youtube.com/embed/VIDEO_ID\n\n"
            "<b>Commands:</b>\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/language - Choose language"
        ),
        "invalid_link": (
            "<b>Invalid YouTube link</b>\n\n"
            "Please send a valid YouTube video URL.\n"
            "Example: https://youtube.com/watch?v=dQw4w9WgXcQ"
        ),
        "processing": (
            "<b>Analyzing video comments...</b>\n\n"
            "This may take 10-30 seconds depending on the number of comments."
        ),
        "video_not_found": (
            "<b>Video not found</b>\n\n"
            "The video might be private, deleted, or the link is incorrect."
        ),
        "analyzing_comments": (
            "<b>Analyzing comments...</b>\n\n"
            "{video_line}\n"
            "{channel_line}\n\n"
            "Fetching comments..."
        ),
        "no_comments": (
            "<b>No comments found</b>\n\n"
            "This video either has no comments or comments are disabled."
        ),
        "found_comments": (
            "<b>Analyzing comments...</b>\n\n"
            "{video_line}\n"
            "{channel_line}\n\n"
            "Found {count} comments. Running AI analysis..."
        ),
        "cannot_access_comments": "<b>Cannot access comments</b>\n\n{error}",
        "error": "<b>Error</b>\n\n{error}",
        "error_occurred": (
            "<b>An error occurred</b>\n\n"
            "Please try again later. If the problem persists, the video might have "
            "too many comments or there might be an API issue."
        ),
        "language_select": "<b>Select language:</b>",
        "language_set": "Language set to <b>{language_name}</b>.",
    },
    "ru": {
        "analysis_complete": "Анализ завершен!",
        "video_label": "Видео",
        "channel_label": "Канал",
        "comments_analyzed": "Проанализировано комментариев",
        "welcome": (
            "<b>Добро пожаловать в YouTube Comment Analyzer!</b>\n\n"
            "Отправьте ссылку на видео YouTube, и я проанализирую комментарии и скажу:\n\n"
            "<b>Преобладающий тип комментариев</b> - какие комментарии встречаются чаще всего\n"
            "<b>Самый популярный тип комментариев</b> - какие комментарии получают больше всего лайков\n\n"
            "Вставьте ссылку на ваше видео сюда, и вы получите сводку по 30 случайным комментариям."
        ),
        "help": (
            "<b>Как пользоваться ботом:</b>\n\n"
            "1. Скопируйте ссылку на видео YouTube\n"
            "2. Отправьте ее сюда\n"
            "3. Дождитесь анализа (обычно 10-30 секунд)\n\n"
            "Вставьте ссылку на ваше видео сюда, и вы получите сводку по 30 случайным комментариям.\n\n"
            "<b>Поддерживаемые форматы ссылок:</b>\n"
            "- https://youtube.com/watch?v=VIDEO_ID\n"
            "- https://youtu.be/VIDEO_ID\n"
            "- https://youtube.com/embed/VIDEO_ID\n\n"
            "<b>Команды:</b>\n"
            "/start - Запустить бота\n"
            "/help - Показать справку\n"
            "/language - Выбрать язык"
        ),
        "invalid_link": (
            "<b>Некорректная ссылка YouTube</b>\n\n"
            "Пожалуйста, отправьте корректный URL видео.\n"
            "Пример: https://youtube.com/watch?v=dQw4w9WgXcQ"
        ),
        "processing": (
            "<b>Анализируем комментарии...</b>\n\n"
            "Это может занять 10-30 секунд в зависимости от количества комментариев."
        ),
        "video_not_found": (
            "<b>Видео не найдено</b>\n\n"
            "Видео может быть приватным, удаленным или ссылка неверна."
        ),
        "analyzing_comments": (
            "<b>Анализируем комментарии...</b>\n\n"
            "{video_line}\n"
            "{channel_line}\n\n"
            "Получаем комментарии..."
        ),
        "no_comments": (
            "<b>Комментарии не найдены</b>\n\n"
            "У этого видео нет комментариев или они отключены."
        ),
        "found_comments": (
            "<b>Анализируем комментарии...</b>\n\n"
            "{video_line}\n"
            "{channel_line}\n\n"
            "Найдено комментариев: {count}. Запускаю анализ..."
        ),
        "cannot_access_comments": "<b>Нет доступа к комментариям</b>\n\n{error}",
        "error": "<b>Ошибка</b>\n\n{error}",
        "error_occurred": (
            "<b>Произошла ошибка</b>\n\n"
            "Пожалуйста, попробуйте позже. Если проблема сохраняется, у видео может быть "
            "слишком много комментариев или есть проблема с API."
        ),
        "language_select": "<b>Выберите язык:</b>",
        "language_set": "Язык установлен: <b>{language_name}</b>.",
    },
}


def get_language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES[DEFAULT_LANGUAGE])


def t(language: str, key: str, **kwargs) -> str:
    selected_language = language if language in STRINGS else DEFAULT_LANGUAGE
    template = STRINGS.get(selected_language, {}).get(key) or STRINGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template
