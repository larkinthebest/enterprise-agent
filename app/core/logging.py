import logging
import sys
from contextvars import ContextVar
from pythonjsonlogger.json import JsonFormatter as _JsonFormatter
from app.core.config import settings

current_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")


class CustomJsonFormatter(_JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["trace_id"] = current_trace_id.get()
        if not log_record.get("timestamp"):
            log_record["timestamp"] = self.formatTime(record, self.datefmt)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(settings.log_level)

    logger.handlers = []

    logHandler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s", rename_fields={"levelname": "level", "name": "logger"}
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)


logger = logging.getLogger(settings.app_name)
