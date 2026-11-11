from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=settings.sql_echo,
                       pool_pre_ping=True, connect_args={"options": "-c timezone=UTC"})


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
