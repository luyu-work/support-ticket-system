"""Тела запросов/ответов для регистрации и входа."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole

class ClientRegistrationRequest(BaseModel):
    """Тело запроса на саморегистрацию клиента."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)

    password: str = Field(min_length=8, max_length=72)

class UserLoginRequest(BaseModel):
    """Тело запроса на вход (клиент, агент или админ)."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

class UserAccountResponse(BaseModel):
    """Безопасные данные пользователя (хеш пароля не отдаём)."""

    model_config = ConfigDict(from_attributes=True)

    user_account_id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_online: bool
    created_at: datetime

    agent_number: int | None = None

class AccessTokenResponse(BaseModel):
    """JWT после успешного входа или регистрации."""

    access_token: str
    token_type: str = "bearer"
    user_account: UserAccountResponse
