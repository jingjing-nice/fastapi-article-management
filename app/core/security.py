# 实现密码的哈希和验证功能

from pwdlib import PasswordHash

import jwt

from datetime import datetime, timedelta, UTC

from app.core.config import get_settings

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")


def hash_password(password):
    """将明文密码转换为哈希，用于保存。"""
    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    """检查用户输入的密码是否匹配保存的哈希。"""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id) -> str:
    settings = get_settings()

    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),  # 用户ID，按照JWT的使用规范
        "iat": now,  # 令牌的开始时间
        "exp": now
        + timedelta(minutes=settings.jwt_access_token_expire_minutes),  # 令牌的结束时间
    }

    encoded_jwt = jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm="HS256"
    )
    return encoded_jwt
