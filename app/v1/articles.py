from fastapi import APIRouter, status, Query, Response, Depends
from typing import Annotated, Literal

from app.core.database import SessionDep

from app.schemas.article import ArticleCreate, ArticlePublic, ArticlePage, ArticleUpdate
from app.services import article_service
from app.core.auth import get_current_user, require_admin, CurrentUserDep

router = APIRouter(
    prefix="/api/v1/articles", tags=["文章"], dependencies=[Depends(get_current_user)]
)


@router.post(
    "",
    response_model=ArticlePublic,  # 定义响应格式
    status_code=status.HTTP_201_CREATED,  # 定义响应状态码
)
def create_article(
    data: ArticleCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    # Implementation for creating an article
    return article_service.create_article(
        data=data, session=session, owner_id=current_user.id
    )


# 查询id


@router.get(
    "/{article_id}",
    response_model=ArticlePublic,
)
def get_article_by_id(
    article_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    return article_service.get_visible_article(
        article_id=article_id,
        session=session,
        owner_id=(None if current_user.role == "admin" else current_user.id),
    )


@router.get(
    "",
    response_model=ArticlePage,
    response_model_exclude_unset=True,
)
def list_articles(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    name: Annotated[str | None, Query(max_length=100)] = None,
    article_status: Annotated[
        Literal["draft", "published"] | None, Query(alias="status")
    ] = None,
):
    return article_service.list_articles(
        session=session,
        owner_id=(None if current_user.role == "admin" else current_user.id),
        page=page,
        page_size=page_size,
        name=name,
        article_status=article_status,
        role=current_user.role,
    )


@router.patch(
    "/{article_id}",
    response_model=ArticlePublic,
)
@router.put(
    "/{article_id}",
    response_model=ArticlePublic,
)
def update_article(
    article_id: int,
    data: ArticleUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    return article_service.update_article(
        article_id=article_id,
        data=data,
        session=session,
        owner_id=(None if current_user.role == "admin" else current_user.id),
    )


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_article(
    article_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    article_service.delete_article(
        article_id=article_id,
        session=session,
        owner_id=(None if current_user.role == "admin" else current_user.id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
