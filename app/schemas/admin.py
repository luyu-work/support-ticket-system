"""Admin: agent management schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


WEEKDAY_LABELS_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class AgentCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    agent_number: int = Field(ge=1, le=9999)
    password: str = Field(min_length=4, max_length=128)
    work_days: list[int] = Field(min_length=1, max_length=7)
    work_time_start: str = Field(min_length=4, max_length=5)
    work_time_end: str = Field(min_length=4, max_length=5)

    @field_validator("work_days")
    @classmethod
    def validate_work_days(cls, value: list[int]) -> list[int]:
        cleaned = sorted({day for day in value if 0 <= day <= 6})
        if not cleaned:
            raise ValueError("Выберите хотя бы один рабочий день")
        return cleaned

    @field_validator("work_time_start", "work_time_end")
    @classmethod
    def validate_time(cls, value: str) -> str:
        text = value.strip()
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError("Время в формате HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Некорректное время")
        return f"{hour:02d}:{minute:02d}"


class AgentUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    agent_number: int | None = Field(default=None, ge=1, le=9999)
    password: str | None = Field(default=None, min_length=4, max_length=128)
    work_days: list[int] | None = Field(default=None, min_length=1, max_length=7)
    work_time_start: str | None = Field(default=None, min_length=4, max_length=5)
    work_time_end: str | None = Field(default=None, min_length=4, max_length=5)

    @field_validator("work_days")
    @classmethod
    def validate_work_days(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        cleaned = sorted({day for day in value if 0 <= day <= 6})
        if not cleaned:
            raise ValueError("Выберите хотя бы один рабочий день")
        return cleaned

    @field_validator("work_time_start", "work_time_end")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError("Время в формате HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Некорректное время")
        return f"{hour:02d}:{minute:02d}"


class AgentAdminResponse(BaseModel):
    user_account_id: int
    email: str
    full_name: str
    agent_number: int | None
    agent_badge: str
    is_active: bool
    is_online: bool
    work_days: list[int]
    work_days_label: str
    work_time_start: str | None
    work_time_end: str | None
    work_time_label: str
    created_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentAdminResponse]
    total_count: int
