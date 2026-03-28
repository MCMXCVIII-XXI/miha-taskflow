from enum import Enum

from pydantic import BaseModel, Field


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    BOTH = "both"


class TokenResponse(BaseModel):
    access_token: str | None = Field(default=None, description="Access Token")
    refresh_token: str | None = Field(default=None, description="Refresh Token")
    token_type: str = Field(default="bearer", description="Token Type")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="Refresh Token")


class AccessTokenRequest(BaseModel):
    access_token: str = Field(description="Access Token")
