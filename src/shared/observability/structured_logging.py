from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a single-line JSON log entry.

    This keeps logs structured even when the global logger formatter is plain
    text, by serializing the entire payload as the log message.
    """

    payload: dict[str, Any] = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    logger.log(level, json.dumps(payload, default=_json_default, separators=(",", ":"), ensure_ascii=False))


def log_exception(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Emit a JSON log entry with an attached exception traceback."""

    payload: dict[str, Any] = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    logger.exception(json.dumps(payload, default=_json_default, separators=(",", ":"), ensure_ascii=False))


def _json_default(value: Any) -> str:
    try:
        return value.isoformat()  # type: ignore[attr-defined]
    except Exception:
        return str(value)
