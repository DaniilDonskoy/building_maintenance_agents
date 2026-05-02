from loguru import logger


class Settings:
    def configure_logging(self) -> None:
        logger.add("logs/house_graph_{time}.log")