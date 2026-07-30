"""Password hashing and JWT helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.settings import ApplicationSettings, get_application_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_plain_password(plain_password: str) -> str:
    """Turn a plain password into a hash for storage."""
    return password_context.hash(plain_password)


def verify_plain_password(plain_password: str, hashed_password: str) -> bool:
    """Check plain password against stored hash."""
    return password_context.verify(plain_password, hashed_password)


def create_access_token(
    token_payload: dict[str, Any],
    settings: ApplicationSettings | None = None,
) -> str:
    """Build a signed JWT access token."""
    application_settings = settings or get_application_settings()
    expire_at = datetime.now(UTC) + timedelta(
        minutes=application_settings.jwt_access_token_expire_minutes,
    )
    payload_to_encode = {**token_payload, "exp": expire_at}
    return jwt.encode(
        payload_to_encode,
        application_settings.jwt_secret_key,
        algorithm=application_settings.jwt_algorithm,
    )


def decode_access_token(
    access_token: str,
    settings: ApplicationSettings | None = None,
) -> dict[str, Any]:
    """
    Decode and validate JWT.
    Raises JWTError if token is invalid or expired.
    """
    application_settings = settings or get_application_settings()
    return jwt.decode(
        access_token,
        application_settings.jwt_secret_key,
        algorithms=[application_settings.jwt_algorithm],
    )
