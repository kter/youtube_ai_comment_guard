"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # GCP Configuration
    google_cloud_project: str = ""
    gcp_region: str = "asia-northeast1"

    # YouTube API
    youtube_credentials: str = ""  # JSON string from Secret Manager

    # Processing Configuration
    toxicity_threshold: int = 70  # Comments above this score are hidden
    hold_threshold: int = 50  # Comments above this are held for review

    # AI Configuration
    gemini_model: str = "gemini-1.5-flash-002"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
