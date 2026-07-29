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

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ticket_admin"
    postgres_password: str = "ticket_secret_change_me"
    postgres_database: str = "ticket_system"

    jwt_secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    log_level: str = "INFO"

    @property
    def database_connection_url(self) -> str:
        """SQLAlchemy URL for PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )


@lru_cache
def get_application_settings() -> ApplicationSettings:
    """One shared settings object for the whole process."""
    return ApplicationSettings()
