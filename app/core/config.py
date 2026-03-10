"""Application configuration."""

from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_DIR = Path(__file__).resolve().parent.parent  # app/
ROOT_DIR = APP_DIR.parent  # repo root


def load_app_env() -> None:
    """Load env files into the process environment for third-party libraries."""

    load_dotenv(APP_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    """Typed application settings loaded from environment or .env."""

    demo_agent_model: str = "gemini-2.5-flash-native-audio-preview-12-2025"
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres"
    database_echo: bool = False
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "postgres"
    gmail_user_id: str = "me"
    gmail_credentials_file: Path = ROOT_DIR / "credentials.json"
    gmail_token_file: Path = ROOT_DIR / "token.json"
    gmail_watch_topic: str = ""
    gmail_watch_label_ids_csv: str = "INBOX"
    gmail_allowed_email_addresses_csv: str = ""
    recall_ai_token: str = ""
    # Region-specific base URL; change to match your Recall AI account region
    # (e.g. us-east-1, eu-west-1).  The ap-northeast-1 default matches the
    # region used during initial development.
    recall_ai_base_url: str = "https://ap-northeast-1.recall.ai/api/v1"
    recall_ai_bot_name: str = "Gemini Agent"

    model_config = SettingsConfigDict(
        env_file=(APP_DIR / ".env", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def gmail_watch_label_ids(self) -> list[str]:
        return [item.strip() for item in self.gmail_watch_label_ids_csv.split(",") if item.strip()]

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@127.0.0.1:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def gmail_allowed_email_addresses(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.gmail_allowed_email_addresses_csv.split(",")
            if item.strip()
        }

    @property
    def gmail_history_types(self) -> list[str]:
        return ["messageAdded"]


load_app_env()
settings = Settings()
settings.database_url = settings.resolved_database_url
