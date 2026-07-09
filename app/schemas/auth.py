from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MemberOut(ORMModel):
    id: int
    name: str
    role: str
    email: EmailStr
    avatar_color: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A nova senha precisa ter pelo menos 8 caracteres")
        return v
