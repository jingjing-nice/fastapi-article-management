from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.exceptions import database_exception_handler
from app.core.logging import configure_logging
from app.v1.articles import router as articles_router

configure_logging(get_settings().log_level)
app = FastAPI(title=get_settings().app_name, version="0.1.0")
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.include_router(articles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
