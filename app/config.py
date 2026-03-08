"""Application configuration."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent


def load_app_env() -> None:
    """Load env files into the process environment for third-party libraries."""

    load_dotenv(APP_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    """Typed application settings loaded from environment or .env."""

    demo_agent_model: str = "gemini-2.5-flash-native-audio-preview-12-2025"

    model_config = SettingsConfigDict(
        env_file=(APP_DIR / ".env", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


load_app_env()
settings = Settings()