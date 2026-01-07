from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ===================== Telegram =====================
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")

    # ===================== YouTube =====================
    youtube_api_key: str = Field(..., description="YouTube Data API key")

    # ===================== OpenAI =====================
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(
        default="gpt-5-nano",
        description="OpenAI model to use",
    )

    # ===================== Webhook =====================
    webhook_url: str | None = Field(
        default=None,
        description="Webhook URL for production",
    )

    # Base URL for internal API calls (bot → FastAPI)
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for API server",
    )

    # ===================== App =====================
    max_comments: int = Field(
        default=30,
        description="Maximum comments to fetch",
    )

    # ===================== Prompts =====================
    comment_prompt_id: str = Field(
        ...,
        description="OpenAI Prompt ID for single comment analysis",
    )
    topic_analysis_prompt_id: str = Field(
        ...,
        description="OpenAI Prompt ID for topic analysis",
    )

    # ===================== Auth (Bot → FastAPI) =====================
    bot_client_id: str = Field(
        ...,
        description="Client ID used by Telegram bot to authenticate",
    )
    bot_client_secret: str = Field(
        ...,
        description="Client secret used by Telegram bot to authenticate",
    )

    jwt_secret: str = Field(
        ...,
        description="Secret key for signing JWT tokens",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_ttl_seconds: int = Field(
        default=900,
        description="JWT lifetime in seconds (default 15 minutes)",
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
