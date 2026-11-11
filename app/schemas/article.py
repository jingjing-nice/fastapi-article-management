# 用于校验客户端提交的文章数据

from sqlmodel import Field, SQLModel

from typing import Literal

from datetime import datetime

"""
没有 table=True：只校验请求数据，不创建表
"""


# 接收、校验请求数据
class ArticleCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "published"] = "draft"


class ArticlePublic(SQLModel):
    id: int
    name: str
    content: str
    summary: str | None
    status: Literal["draft", "published"]
    created_at: datetime
    updated_at: datetime


class ArticlePage(SQLModel):
    total: int
    items: list[ArticlePublic]
    page: int
    page_size: int


class ArticleUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "published"] | None = None
