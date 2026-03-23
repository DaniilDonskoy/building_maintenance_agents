import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from loguru import logger
from contextlib import asynccontextmanager

# from api.errors.http_error import http_error_handler
from .api import api_router
from .config import get_app_settings
from .middlewares import LoggingMiddleware


async def on_startup():
    logger.info("Application startup complete")


async def on_shutdown():
    logger.info("Application shutdown")


def get_application() -> FastAPI:

    settings = get_app_settings()
    settings.configure_logging()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        await on_startup()
        yield
        # Shutdown
        await on_shutdown()
    
    application = FastAPI(**settings.fastapi_kwargs, lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "Content-Type", "multipart/form-data"],
    )

    # application.add_exception_handler(HTTPException, http_error_handler)

    # temporary
    # application.add_exception_handler(
    #     RequestValidationError, http422_error_handler)

    application.add_middleware(LoggingMiddleware)

    application.include_router(api_router)

    return application


app = get_application()