from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.article import Article


import pytest
from fastapi.testclient import TestClient


def test_create_article(client: TestClient, db_session: Session):
    response = client.post(
        "/api/v1/articles",
        json={
            "name": "自动化测试文章",
            "content": "测试正文",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert isinstance(data["id"], int)
    assert data["name"] == "自动化测试文章"
    assert data["content"] == "测试正文"
    assert data["summary"] is None
    assert data["status"] == "draft"
    assert data["created_at"]
    assert data["updated_at"]

    db_session.expire_all()
    article = db_session.get(Article, data["id"])

    assert article is not None
    assert article.name == "自动化测试文章"
    assert article.content == "测试正文"


@pytest.mark.parametrize(
    "payload, error_field",
    [
        ({"content": "正文"}, "name"),
        ({"name": "", "content": "正文"}, "name"),
        ({"name": "标题"}, "content"),
        ({"name": "标题", "content": ""}, "content"),
        (
            {"name": "标题", "content": "正文", "status": "abc"},
            "status",
        ),
    ],
)
def test_create_article_invalid(
    client: TestClient,
    payload: dict,
    error_field: str,
):
    response = client.post("/api/v1/articles", json=payload)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", error_field] for error in errors)
