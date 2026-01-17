"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Environment
    environment: str = "dev"

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

    # Frontend URLs for CORS
    frontend_url: str = ""  # Set via environment variable

    @property
    def allowed_origins(self) -> list[str]:
        """Get allowed CORS origins based on environment."""
        origins = []

        # Add configured frontend URL
        if self.frontend_url:
            origins.append(self.frontend_url)

        # Environment-specific defaults
        if self.environment == "dev":
            origins.extend([
                "https://youtube-comment-guard.dev.devtools.site",
                "http://localhost:5173",  # Vite dev server
                "http://localhost:3000",
            ])
        elif self.environment == "prd":
            origins.append("https://youtube-comment-guard.devtools.site")

        return list(set(origins))  # Remove duplicates

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
