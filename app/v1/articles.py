from fastapi import APIRouter, status, Query, Response
from typing import Annotated, Literal

from app.core.database import SessionDep

from app.schemas.article import ArticleCreate, ArticlePublic, ArticlePage, ArticleUpdate
from app.services import article_service

router = APIRouter(
    prefix="/api/v1/articles",
    tags=["文章"],
)


@router.post(
    "",
    response_model=ArticlePublic,  # 定义响应格式
    status_code=status.HTTP_201_CREATED,  # 定义响应状态码
)
def create_article(data: ArticleCreate, session: SessionDep):
    # Implementation for creating an article
    return article_service.create_article(data=data, session=session)


# 查询id


@router.get("/{article_id}", response_model=ArticlePublic)
def get_article_by_id(article_id: int, session: SessionDep):
    return article_service.get_article_by_id(article_id=article_id, session=session)


@router.get("", response_model=ArticlePage)
def list_articles(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    name: Annotated[str | None, Query(max_length=100)] = None,
    sort: Literal["created_at", "-created_at", "updated_at", "-updated_at"] | None = None,
    article_status: Annotated[
        Literal["draft", "published"] | None, Query(alias="status")
    ] = None,
):
    return article_service.list_articles(
        session=session,
        page=page,
        page_size=page_size,
        name=name,
        article_status=article_status,
        sort=sort,
    )


@router.patch("/{article_id}", response_model=ArticlePublic)
@router.put("/{article_id}", response_model=ArticlePublic)
def update_article(
    article_id: int,
    data: ArticleUpdate,
    session: SessionDep,
):
    return article_service.update_article(
        article_id=article_id, data=data, session=session
    )


@router.delete(
    "/{article_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_article(article_id: int, session: SessionDep):
    article_service.delete_article(article_id=article_id, session=session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
