# Code above omitted 👆
from sqlmodel import Session, select, col
from sqlalchemy import func
from app.models.article import Article
from typing import Any


# 编写新增文章的数据访问方
def create_article(article: Article, session: Session) -> Article:
    session.add(article)  # 将文章对象添加到数据库会话中
    session.flush()  ## 执行数据库写入，但尚未提交事务
    session.refresh(article)  # 从数据库重新读取文章字段。
    return article


# 查询文章
def get_article_by_id(article_id: int, session: Session) -> Article | None:
    return session.get(Article, article_id)


def filtered_articles(
    name: str | None,
    article_status: str | None,
    owner_id: int | None,
):
    filters = []

    if owner_id is not None:
        filters.append(Article.owner_id == owner_id)

    if name:
        filters.append(col(Article.name).contains(name, autoescape=True))
    if article_status is not None:
        filters.append(Article.status == article_status)
    return filters


def list_articles(
    session: Session,
    owner_id: int | None,
    offset: int = 0,
    limit: int = 10,
    name: str | None = None,
    article_status: str | None = None,
    sort: str | None = None,
) -> list[Article]:
    statement = select(Article).where(
        *filtered_articles(name, article_status, owner_id)
    )
    if sort:
        column = {
            "created_at": col(Article.created_at),
            "updated_at": col(Article.updated_at),
        }[sort.lstrip("-")]
        descending = sort.startswith("-")
        statement = statement.order_by(
            column.desc() if descending else column.asc(),
            col(Article.id).desc() if descending else col(Article.id).asc(),
        )
    else:
        statement = statement.order_by(Article.id)
    return list(session.exec(statement.offset(offset).limit(limit)).all())


def count_articles(
    session: Session,
    owner_id: int | None,
    name: str | None = None,
    article_status: str | None = None,
) -> int:
    statement = (
        select(func.count())
        .select_from(Article)
        .where(*filtered_articles(name, article_status, owner_id))
    )
    return session.exec(statement).one()


# 更新文章
# changes：经过 Service 检查、需要修改的字段。
def update_article(
    session: Session, article: Article, changes: dict[str, Any]
) -> Article:
    article.sqlmodel_update(changes)  # 更新文章对象的属性
    session.add(article)  # 将文章对象添加到数据库会话中
    session.flush()  ## 执行数据库写入，但尚未提交事务
    session.refresh(article)  # 从数据库重新读取文章字段。
    return article


# 删除文章


def delete_article(session: Session, article: Article) -> None:
    session.delete(article)
    session.flush()  # 执行数据库写入，但尚未提交事务
