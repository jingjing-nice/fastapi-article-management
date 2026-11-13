from collections.abc import Generator

import pytest
from sqlalchemy import URL
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from app.core.config import Settings
from app.models.article import Article  # noqa: F401

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.main import app
from app.core.auth import get_current_user
from app.models.user import Users


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    settings = Settings()

    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database="articles_test",
    )

    engine = create_engine(url)

    try:
        SQLModel.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session
        finally:
            transaction.rollback()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_session():
        yield db_session

    user = Users(username="test-reader", password_hash="unused", role="user")
    db_session.add(user)
    db_session.flush()

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides = previous_overrides
