from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class ApplicationSettings(BaseSettings):
    """Все настройки приложения (из env / .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    application_name: str = "support-ticket-system"
    application_environment: str = "local"
    application_debug: bool = True

    database_url_override: str | None = None

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ticket_admin"
    postgres_password: str = "ticket_secret_change_me"
    postgres_database: str = "ticket_system"

    jwt_secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    seed_staff_on_startup: bool = True
    seed_admin_email: str = "root@gmail.com"
    seed_admin_password: str = "root"
    seed_admin_full_name: str = "Харисов Данил Мансурович"
    seed_agent_email: str = "agent_1@gmail.com"
    seed_agent_password: str = "agent_1"
    seed_agent_full_name: str = "Денисов Игорь Сергеевич"

    log_level: str = "INFO"

    ticket_uploads_directory: str = "uploads/ticket_attachments"
    max_ticket_photo_size_bytes: int = 5 * 1024 * 1024

    @property
    def database_connection_url(self) -> str:
        """URL для SQLAlchemy: свой (SQLite/Postgres) или PostgreSQL по умолчанию."""
        override = (self.database_url_override or "").strip()
        if override:
            return override

        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    @property
    def uses_sqlite_database(self) -> bool:
        return self.database_connection_url.startswith("sqlite")

@lru_cache
def get_application_settings() -> ApplicationSettings:
    """Один общий объект настроек на весь процесс."""
    return ApplicationSettings()
