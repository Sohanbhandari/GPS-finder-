import logging
import re
import sys
from app.core.config import settings


class SecretMaskingFormatter(logging.Formatter):
    """
    Custom log formatter that masks sensitive strings such as passwords or secret keys.
    """
    SENSITIVE_PATTERNS = [
        (re.compile(r"password=([^\s&'\"]+)", re.IGNORECASE), "password=***MASKED***"),
        (re.compile(r"JWT_SECRET_KEY=([^\s&'\"]+)", re.IGNORECASE), "JWT_SECRET_KEY=***MASKED***"),
        (re.compile(r"://([^:]+):([^@]+)@", re.IGNORECASE), r"://\1:***MASKED***@"),
    ]

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = pattern.sub(replacement, formatted)
        return formatted


def setup_logging() -> logging.Logger:
    """
    Initializes application logging with standard formatting and security masking.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger("gps_tracker")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = SecretMaskingFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logging()
