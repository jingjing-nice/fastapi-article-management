# 负责转换请求数据和管理事务

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.models.article import Article
from app.repositories import article_repository
from app.schemas.article import ArticleCreate, ArticlePage, ArticlePublic, ArticleUpdate

from fastapi import HTTPException, status

from typing import Any


def create_article(data: ArticleCreate, session: Session) -> Article:

    article = Article.model_validate(data)  # 将请求数据转换为 Article 模型对象

    try:
        article_repository.create_article(article=article, session=session)

        # 提交事务
        session.commit()

    except SQLAlchemyError:
        # 回滚事务
        session.rollback()
        # 不加raise 否则数据库写入失败后，代码仍会继续执行 refresh()，掩盖原始错误
        raise

    session.refresh(article)  # 从数据库重新读取文章字段。
    return article


# 查询文章
def get_article_by_id(article_id: int, session: Session) -> Article:

    article = article_repository.get_article_by_id(
        article_id=article_id, session=session
    )
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )

    return article


# 获取文章列表
def list_articles(
    session: Session,
    page: int = 1,  # 页码
    page_size: int = 10,  # 每页数量
    name: str | None = None,  # 搜索关键词
    article_status: str | None = None,  # 搜索文章状态
    sort: str | None = None,
) -> ArticlePage:
    offset = (page - 1) * page_size

    articles = article_repository.list_articles(
        session=session,
        offset=offset,
        limit=page_size,
        name=name,
        article_status=article_status,
        sort=sort,
    )

    total = article_repository.count_articles(
        session=session, name=name, article_status=article_status
    )

    return ArticlePage(
        items=[ArticlePublic.model_validate(article) for article in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


# 更新文章
def update_article(session: Session, article_id: int, data: ArticleUpdate) -> Article:
    # 查询文章是否存在
    article = get_article_by_id(article_id=article_id, session=session)

    # # 只提取请求中实际提交的字段，保留显式提交的 None
    changes = data.model_dump(exclude_unset=True)

    for field in ("name", "content", "status"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{field} 不能为 null",
            )

    if not changes:
        return article  # 如果没有需要更新的字段，直接返回原始文章对象
    try:
        article_repository.update_article(
            session=session, article=article, changes=changes
        )
        # 提交事务
        session.commit()

    except SQLAlchemyError:
        # 回滚事务
        session.rollback()
        raise

    session.refresh(article)  # 从数据库重新读取文章字段。
    return article


# 删除文章
def delete_article(session: Session, article_id: int) -> None:
    # 查询文章是否存在
    article = get_article_by_id(article_id=article_id, session=session)

    try:
        article_repository.delete_article(session=session, article=article)
        # 提交事务
        session.commit()

    except SQLAlchemyError:
        # 回滚事务
        session.rollback()
        raise
