from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from typing import Annotated

from app.core.database import SessionDep
from app.schemas.user import UserCreate, UserPublic, Token
from app.services.user_service import register_user, login_user
from app.core.config import get_settings
from app.core.auth import CurrentUserDep


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["身份认证"],
)


@router.post("/register", response_model=UserPublic)
def register(data: UserCreate, session: SessionDep):
    return register_user(data, session)


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> str:

    access_token = login_user(
        username=form_data.username,
        password=form_data.password,
        session=session,
    )

    return Token(
        access_token=access_token,
        expires_in=(get_settings().jwt_access_token_expire_minutes * 60),
    )


@router.get("/me", response_model=UserPublic)
def get_me(current_user: CurrentUserDep):
    return current_user
