from fastapi import HTTPException, status

from sqlmodel import Session, select

from sqlalchemy.exc import IntegrityError

from app.models.user import Users
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token


def register_user(data: UserCreate, session: Session) -> Users:
    # 检查用户名是否已存在
    existing_user = session.exec(
        select(Users).where(Users.username == data.username)
    ).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    user = Users(
        username=data.username,
        password_hash=hash_password(data.password),
        role="user",
        is_active=True,
    )

    session.add(user)
    try:
        # 提交事务
        session.commit()

    except IntegrityError:
        # 回滚事务
        session.rollback()

        existing_user = session.exec(
            select(Users).where(Users.username == data.username)
        ).first()

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            ) from None

        # 不加raise 否则数据库写入失败后，代码仍会继续执行 refresh()，掩盖原始错误
        raise

    session.refresh(user)  # 从数据库重新读取用户字段。
    return user


def login_user(username: str, password: str, session: Session):
    username = username.strip().lower()

    user = session.exec(select(Users).where(Users.username == username)).first()

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise credentials_error

    if not verify_password(password, user.password_hash):
        raise credentials_error

    if not user.is_active:
        raise credentials_error

    return create_access_token(user_id=user.id)
