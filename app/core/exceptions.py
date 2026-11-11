import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Database operation failed: %s %s", request.method, request.url.path,
                 exc_info=(type(exc), exc, exc.__traceback__))
    return JSONResponse(status_code=500, content={"detail": "数据库操作失败"})
