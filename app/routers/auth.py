from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.security import (
    CurrentMember,
    DbSession,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.member import Member
from app.schemas.auth import ChangePasswordRequest, LoginRequest, MemberOut, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _authenticate(db, email: str, password: str) -> Member:
    result = await db.execute(select(Member).where(Member.email == email))
    member = result.scalar_one_or_none()
    if member is None or not member.active or not verify_password(password, member.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos"
        )
    return member


@router.post("/login", response_model=TokenResponse)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    """Login padrão OAuth2 (username = e-mail). Usado também pelo Swagger."""
    member = await _authenticate(db, form.username, form.password)
    return TokenResponse(access_token=create_access_token(member.id))


@router.post("/login-json", response_model=TokenResponse)
async def login_json(payload: LoginRequest, db: DbSession):
    """Login em JSON, usado pelo frontend Angular."""
    member = await _authenticate(db, payload.email, payload.password)
    return TokenResponse(access_token=create_access_token(member.id))


@router.get("/me", response_model=MemberOut)
async def me(current: CurrentMember):
    return current


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(payload: ChangePasswordRequest, current: CurrentMember, db: DbSession):
    if not verify_password(payload.current_password, current.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta")
    current.hashed_password = hash_password(payload.new_password)
    db.add(current)
    await db.commit()
