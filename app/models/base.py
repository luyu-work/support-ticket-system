"""Реэкспорт базы, чтобы модели импортировали из app.models.base."""

from app.core.database import DatabaseModelBase

__all__ = ["DatabaseModelBase"]
