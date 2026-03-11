from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str | None = Field(default=None, alias="Access Token")
    refresh_token: str | None = Field(default=None, alias="Refresh Token")
    token_type: str = Field(default="bearer", alias="Token Type")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(alias="Refresh Token")


class AccessTokenRequest(BaseModel):
    access_token: str = Field(alias="Access Token")
