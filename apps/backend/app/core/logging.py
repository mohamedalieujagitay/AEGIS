"""Structured application logging.

Records are written to standard output, either as one JSON object per line
(the default, for log collection) or as readable text for local use. Every
record carries a timestamp, level, logger name, service name, optional
event type and the current request ID (SYSTEM_ARCHITECTURE.md §13.1).

Sensitive data: never put passwords, tokens, secrets, session identifiers or
request bodies into log messages. As a safety net, structured fields whose
names look sensitive are redacted.
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any, Final

from app.core.config import Settings
from app.core.request_context import request_id_var

SERVICE_NAME: Final = "aegis-api"
HANDLER_NAME: Final = "aegis"
REDACTED: Final = "[REDACTED]"
HTTP_CLIENT_LOGGERS: Final = ("httpx", "httpx2", "httpcore", "httpcore2")

SENSITIVE_KEY = re.compile(
    r"pass(word|wd)?|secret|token|authori[sz]ation|cookie|session|api[_-]?key|credential|private[_-]?key",
    re.IGNORECASE,
)

# Attributes every LogRecord has; anything else was passed through ``extra``.
# Uvicorn's ``color_message`` (terminal colour codes) is excluded as noise.
_STANDARD_ATTRIBUTES: Final = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__
) | {"message", "asctime", "taskName", "color_message"}


def _extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key in _STANDARD_ATTRIBUTES or key.startswith("_"):
            continue
        fields[key] = REDACTED if SENSITIVE_KEY.search(key) else value
    return fields


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every record.

    An ID passed explicitly through ``extra`` is kept: some code, such as the
    unexpected-error handler, runs after the request context has ended.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(record, "request_id", None) is None:
            record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Format records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }
        entry.update(_extra_fields(record))
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "traceback": self.formatException(record.exc_info),
            }
        return json.dumps(entry, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Readable single-line format for local development."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-7s %(name)s [%(request_id)s] %(message)s")


def configure_logging(settings: Settings) -> None:
    """Route application and server logs through one handler.

    Safe to call more than once: the AEGIS handler is replaced, and handlers
    added by others (for example test harnesses) are kept.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.set_name(HANDLER_NAME)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter() if settings.log_format == "json" else TextFormatter())

    root = logging.getLogger()
    for existing in list(root.handlers):
        if existing.get_name() == HANDLER_NAME:
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    # Uvicorn's own loggers go through the same handler. Its access log is
    # disabled because RequestContextMiddleware logs each request without the
    # query string, which Uvicorn's access log includes.
    for name in ("uvicorn", "uvicorn.error"):
        server_logger = logging.getLogger(name)
        server_logger.handlers.clear()
        server_logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True

    # HTTP client libraries log full request URLs, including query strings,
    # at INFO. Only their warnings and errors are kept.
    for name in HTTP_CLIENT_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
