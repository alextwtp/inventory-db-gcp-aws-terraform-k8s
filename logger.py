# core/logger.py
import logging
import json
import sys
from datetime import datetime, timezone

class UniversalJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "source_location": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
        }
        if hasattr(record, "custom_fields") and isinstance(record.custom_fields, dict):
            log_payload.update(record.custom_fields)
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload, ensure_ascii=False)

def setup_logger(name: str = "inventory_app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(UniversalJsonFormatter())
        logger.addHandler(handler)
    return logger

logger = setup_logger()