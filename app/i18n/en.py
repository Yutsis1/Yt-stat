STRINGS_EN = {
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
        "request_timeout": (
            "<b>Request timed out</b>\n\n"
            "Request to external services timed out. Please try again later."
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
        "menu_change_language": "🌍 Change language",
        "menu_help": "ℹ️ Help",
        "language_set": "Language set to <b>{language_name}</b>.",
        "authorize_success": "App authorized — ready to go!",
        "authorize_failed": "Authorization failed. Please try /start again or contact the administrator.",
        "please_authorize": "Please send /start to authorize the bot before using this command.",
        "comments_by_sentiment_title": "Comments by sentiment:",
        "likes_by_sentiment_title": "Likes by sentiment (total likes):",
        "sentiment_positive": "Positive",
        "sentiment_negative": "Negative",
        "sentiment_neutral": "Neutral",
        "sentiment_nonsensical": "Nonsensical",
        "sentiment_off_topic": "Off-topic",
        "feedback_cta": "Help us improve: please fill out this short form.",
        "feedback_button": "Share feedback",
    },
} 