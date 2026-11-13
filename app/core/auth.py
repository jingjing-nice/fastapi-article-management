# 实现密码的哈希和验证功能


from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError


from app.core.config import get_settings
from app.core.database import SessionDep
from app.models.user import Users


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
):

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录凭证无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]},
        )

        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise credentials_error

        """
        isascii()：只接受 ASCII 字符，排除特殊 Unicode 数字。
        isdecimal()：要求全部是十进制数字，排除 "abc"、`"-1"`。
        长度限制：避免转换特别长的数字字符串
        """
        if not subject.isascii() or not subject.isdecimal() or len(subject) > 19:
            raise credentials_error

        user_id = int(subject)

        if not 0 < user_id <= 2_147_483_647:
            raise credentials_error

    except InvalidTokenError:
        raise credentials_error from None

    user = session.get(Users, user_id)

    if user is None or not user.is_active:
        raise credentials_error

    return user


CurrentUserDep = Annotated[Users, Depends(get_current_user)]


def require_admin(current_user: CurrentUserDep) -> Users:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return current_user
