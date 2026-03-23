from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"{request.method} {request.url.path}")
        response = await call_next(request)
        # logger.info(f"Status code: {response.status_code}")
        return response