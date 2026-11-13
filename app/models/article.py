from sqlmodel import Field, SQLModel

from datetime import UTC, datetime

from sqlalchemy import DateTime


def get_current_time() -> datetime:
    return datetime.now(UTC)


# table=True：这个类用于映射数据库表。
class Article(SQLModel, table=True):
    __tablename__ = "articles"  # 明确指定表名为 articles

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True)
    content: str
    summary: str | None = Field(default=None, max_length=500)
    status: str = Field(
        default="draft", max_length=20, index=True
    )  # 默认草稿，index=True 为该列声明索引

    created_at: datetime = Field(
        default_factory=get_current_time,
        sa_type=DateTime(timezone=True),
        index=True,
    )

    updated_at: datetime = Field(
        default_factory=get_current_time,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": get_current_time},
    )

    # foreign_key声明是外建，index记录是索引
    owner_id: int | None = Field(default=None, foreign_key="users.id", index=True)


# Code below omitted 👇
