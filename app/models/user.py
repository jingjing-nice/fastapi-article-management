from sqlmodel import Field, SQLModel

from datetime import UTC, datetime

from sqlalchemy import DateTime, CheckConstraint


def get_current_time() -> datetime:
    return datetime.now(UTC)


# table=True：这个类用于映射数据库表。
class Users(SQLModel, table=True):
    __tablename__ = "users"  # 明确指定表名
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'admin')",
            name="ck_users_role",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="user", max_length=20)  # 用户角色，默认为普通用户
    created_at: datetime = Field(
        default_factory=get_current_time, sa_type=DateTime(timezone=True)
    )
    is_active: bool = Field(default=True)  # 用户是否激活，默认为 True
