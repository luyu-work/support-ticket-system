"""Request/response bodies for registration and login."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class ClientRegistrationRequest(BaseModel):
    """Body for client self-registration."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """Body for login (client, agent, or admin)."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserAccountResponse(BaseModel):
    """Safe user data (never returns password hash)."""

    model_config = ConfigDict(from_attributes=True)

    user_account_id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_online: bool
    created_at: datetime


class AccessTokenResponse(BaseModel):
    """JWT returned after successful login or registration."""

    access_token: str
    token_type: str = "bearer"
    user_account: UserAccountResponse
