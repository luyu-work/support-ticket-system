from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """All runtime settings for the ticket system (from env / .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    application_name: str = "support-ticket-system"
    application_environment: str = "local"
    application_debug: bool = True

    # If set, used as-is (example: sqlite:///./ticket_system_local.db)
    # If empty — build PostgreSQL URL from fields below.
    database_url_override: str | None = None

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ticket_admin"
    postgres_password: str = "ticket_secret_change_me"
    postgres_database: str = "ticket_system"

    jwt_secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Default staff accounts (created once on API startup if missing)
    seed_staff_on_startup: bool = True
    seed_admin_email: str = "root@gmail.com"
    seed_admin_password: str = "root"
    seed_admin_full_name: str = "Харисов Данил Мансурович"
    seed_agent_email: str = "agent_1@gmail.com"
    seed_agent_password: str = "agent_1"
    seed_agent_full_name: str = "Денисов Игорь Сергеевич"

    log_level: str = "INFO"

    # Ticket photo uploads (relative to project root)
    ticket_uploads_directory: str = "uploads/ticket_attachments"
    max_ticket_photo_size_bytes: int = 5 * 1024 * 1024  # 5 MB per file

    @property
    def database_connection_url(self) -> str:
        """SQLAlchemy URL: override (SQLite/Postgres) or default PostgreSQL."""
        if self.database_url_override:
            return self.database_url_override

        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    @property
    def uses_sqlite_database(self) -> bool:
        return self.database_connection_url.startswith("sqlite")


@lru_cache
def get_application_settings() -> ApplicationSettings:
    """One shared settings object for the whole process."""
    return ApplicationSettings()
