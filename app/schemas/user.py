from sqlmodel import Field, SQLModel

from datetime import UTC, datetime

from pydantic import ConfigDict, field_validator

from typing import Literal


def get_current_time() -> datetime:
    return datetime.now(UTC)


# 接收注册参数。用户名先去除首尾空格、转小写，再检查长度；密码保持原
class UserCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    username: str = Field(max_length=50, min_length=3)
    password: str = Field(max_length=255, min_length=6)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class UserPublic(SQLModel):
    id: int
    username: str
    role: Literal["user", "admin"]
    is_active: bool
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
