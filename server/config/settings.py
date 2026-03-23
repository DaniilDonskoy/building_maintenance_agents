import sys
import logging
from typing import List
from typing import Any, Dict
from dotenv import load_dotenv, find_dotenv

from .logging import InterceptHandler
from pydantic import Field
from pydantic_settings import BaseSettings
from loguru import logger


load_dotenv(find_dotenv(".env"))


class AppSettings(BaseSettings):

    debug: bool = True
    docs_url: str = "/"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = 'API'
    version: str = '0.0.1'

    api_prefix: str = "/api/v1"

    allow_origins: List[str] = Field(alias='ALLOW_ORIGINS')

    logging_level: int = logging.DEBUG
    loggers: tuple = ("uvicorn.asgi", "uvicorn.access")

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        return {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "openapi_prefix": self.openapi_prefix,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
        }

    def configure_logging(self) -> None:

        # disable uvicorn loggers
        uvicorn_error = logging.getLogger("uvicorn.error")
        uvicorn_error.disabled = True

        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_access.disabled = True

        logging.getLogger().handlers = [InterceptHandler()]
        for logger_name in self.loggers:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = [
                InterceptHandler(level=self.logging_level)]

        logger.configure(
            handlers=[{"sink": sys.stderr, "level": self.logging_level}])

        logger.add("server_logs/server_{time}.log",
                   rotation="00:00", compression="zip")
