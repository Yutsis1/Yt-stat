from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    
    # YouTube
    youtube_api_key: str = Field(..., description="YouTube Data API key")
    
    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-5-nano", description="OpenAI model to use")
    
    # Webhook (optional, for production)
    webhook_url: str | None = Field(default=None, description="Webhook URL for production")
    
    # App settings
    max_comments: int = Field(default=100, description="Maximum comments to fetch")

    # Prompt ID for single comment analysis
    comment_prompt_id: str = Field(
        default=...,
        description="OpenAI Prompt ID for single comment analysis"
    )
    # Prompt ID for topic analysis
    topic_analysis_prompt_id: str = Field(
        default=...,
        description="OpenAI Prompt ID for topic analysis"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
