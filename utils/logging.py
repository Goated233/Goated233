import logging
from pythonjsonlogger import jsonlogger


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    logging.basicConfig(level=level, handlers=[handler], force=True)
