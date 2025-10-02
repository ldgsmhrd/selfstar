import logging
import sys

LOG_LEVEL = logging.getLevelName("INFO")

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)

logger = logging.getLogger("app")
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)

__all__ = ["logger"]
