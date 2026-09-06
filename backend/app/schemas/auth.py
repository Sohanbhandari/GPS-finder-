from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Credentials payload for user authentication.
    """
    email: EmailStr = Field(..., description="User login email address")
    password: str = Field(..., min_length=1, description="User password")


class TokenResponse(BaseModel):
    """
    JWT access token response model.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration duration in seconds")


class UserResponse(BaseModel):
    """
    Public representation of a system user.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
