from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_text

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


class JsonlFileProcessor:
    def __init__(self) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def __call__(
        self,
        logger: structlog.typing.WrappedLogger,
        method_name: str,
        event_dict: structlog.typing.EventDict,
    ) -> structlog.typing.EventDict:
        rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{rendered}\n")
        return event_dict



def scrub_event(
    _: structlog.typing.WrappedLogger,
    __: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    payload = event_dict.get("payload")
    if isinstance(payload, dict):
        event_dict["payload"] = {
            k: scrub_text(v) if isinstance(v, str) else v for k, v in payload.items()
        }
    if "event" in event_dict and isinstance(event_dict["event"], str):
        event_dict["event"] = scrub_text(event_dict["event"])
    return event_dict



def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    processors: list[structlog.typing.Processor] = [
        merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
        scrub_event,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        JsonlFileProcessor(),
        structlog.processors.JSONRenderer(),
    ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )



def get_logger() -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger()


def get_audit_logger() -> logging.Logger:
    """Return a dedicated logger that writes JSON lines to AUDIT_LOG_PATH.

    Audit events are NOT scrubbed — they intentionally capture who did what
    (user_id_hash, action, outcome) for compliance purposes. Raw PII must
    never reach this logger; callers must hash/redact before logging.
    """
    logger = logging.getLogger("audit")
    if logger.handlers:
        return logger  # already configured (e.g. on reload)

    logger.setLevel(logging.INFO)
    logger.propagate = False  # don't bubble up to root logger

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(AUDIT_LOG_PATH, encoding="utf-8")

    import json
    from datetime import datetime, timezone

    class _JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            data = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname.lower(),
                **record.msg,
            }
            return json.dumps(data, ensure_ascii=False)

    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    return logger