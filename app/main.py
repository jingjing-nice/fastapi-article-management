from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import database_exception_handler
from app.core.logging import configure_logging
from app.v1.articles import router as articles_router
from app.v1.auth import router as auth_router

configure_logging(get_settings().log_level)
app = FastAPI(title=get_settings().app_name, version="0.1.0")
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.include_router(articles_router)
app.include_router(auth_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
