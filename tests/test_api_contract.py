import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.core.database import get_session
from app.main import app


@pytest.fixture
def api():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    def session_override():
        with Session(engine) as session:
            yield session
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = session_override
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides = previous
        engine.dispose()


def create(api, **fields):
    response = api.post('/api/v1/articles', json={'name': 'Python', 'content': '正文', **fields})
    assert response.status_code == 201
    return response.json()


def test_delete_contract(api):
    article = create(api)
    response = api.delete(f'/api/v1/articles/{article["id"]}')
    assert response.status_code == 204
    assert response.content == b''
    assert api.delete(f'/api/v1/articles/{article["id"]}').status_code == 404


def test_patch_contract(api):
    article = create(api, summary='摘要')
    path = f'/api/v1/articles/{article["id"]}'
    response = api.patch(path, json={'summary': None})
    assert response.status_code == 200
    assert response.json()['summary'] is None
    assert response.json()['name'] == article['name']
    for field in ('name', 'content', 'status'):
        assert api.patch(path, json={field: None}).status_code == 422
    assert api.put(path, json={'content': '更新'}).json()['content'] == '更新'
    assert api.get(path).json()['content'] == '更新'


def test_filters_sort_and_pagination(api):
    first = create(api, name='100% Python', status='published')
    second = create(api, name='Python other')
    assert api.get('/api/v1/articles', params={'name': '%', 'status': 'published'}).json()['total'] == 1
    for sort in ('created_at', 'updated_at', '-created_at', '-updated_at'):
        response = api.get('/api/v1/articles', params={'sort': sort, 'page_size': 1})
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['items']) == 1
        assert data['items'][0]['id'] == (second if sort.startswith('-') else first)['id']
    assert api.get('/api/v1/articles', params={'sort': 'unsafe'}).status_code == 422
    for params in ({'page': 0}, {'page_size': 101}, {'status': 'invalid'}):
        assert api.get('/api/v1/articles', params=params).status_code == 422
    assert api.get('/api/v1/articles?page=10').json()['items'] == []


def test_database_error_is_generic_and_rolls_back(api, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from app.repositories import article_repository
    original = article_repository.create_article
    def fail(article, session):
        original(article, session)
        raise SQLAlchemyError('secret connection details')
    monkeypatch.setattr(article_repository, 'create_article', fail)
    response = api.post('/api/v1/articles', json={'name': 'test', 'content': 'body'})
    assert response.status_code == 500
    assert response.json() == {'detail': '数据库操作失败'}
    assert api.get('/api/v1/articles').json()['total'] == 0


def test_openapi(api):
    schema = api.get('/openapi.json').json()
    assert 'patch' in schema['paths']['/api/v1/articles/{article_id}']
    assert api.get('/api/v1/articles/999999').status_code == 404
