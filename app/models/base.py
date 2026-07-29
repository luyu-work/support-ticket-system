"""Re-export base so models can import from app.models.base."""

from app.core.database import DatabaseModelBase

__all__ = ["DatabaseModelBase"]
