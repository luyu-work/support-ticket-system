"""Admin: agent management schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

WEEKDAY_LABELS_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def validate_work_days(value: list[int]) -> list[int]:
    cleaned = sorted({day for day in value if 0 <= day <= 6})
    if not cleaned:
        raise ValueError("Выберите хотя бы один рабочий день")
    return cleaned


def validate_hh_mm(value: str) -> str:
    text = value.strip()
    parts = text.split(":")
    if len(parts) != 2:
        raise ValueError("Время в формате HH:MM")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Некорректное время")
    return f"{hour:02d}:{minute:02d}"


class AgentCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    agent_number: int = Field(ge=1, le=9999)
    email: EmailStr
    password: str = Field(min_length=4, max_length=72)
    work_days: list[int] = Field(min_length=1, max_length=7)
    work_time_start: str = Field(min_length=4, max_length=5)
    work_time_end: str = Field(min_length=4, max_length=5)

    @field_validator("email")
    @classmethod
    def _email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("work_days")
    @classmethod
    def _days(cls, value: list[int]) -> list[int]:
        return validate_work_days(value)

    @field_validator("work_time_start", "work_time_end")
    @classmethod
    def _time(cls, value: str) -> str:
        return validate_hh_mm(value)


class AgentUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    agent_number: int | None = Field(default=None, ge=1, le=9999)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=4, max_length=72)
    work_days: list[int] | None = Field(default=None, min_length=1, max_length=7)
    work_time_start: str | None = Field(default=None, min_length=4, max_length=5)
    work_time_end: str | None = Field(default=None, min_length=4, max_length=5)

    @field_validator("email")
    @classmethod
    def _email(cls, value: EmailStr | None) -> str | None:
        return None if value is None else str(value).strip().lower()

    @field_validator("work_days")
    @classmethod
    def _days(cls, value: list[int] | None) -> list[int] | None:
        return None if value is None else validate_work_days(value)

    @field_validator("work_time_start", "work_time_end")
    @classmethod
    def _time(cls, value: str | None) -> str | None:
        return None if value is None else validate_hh_mm(value)


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
    password: str | None = None
    created_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentAdminResponse]
    total_count: int
