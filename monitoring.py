from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

_logger = logging.getLogger("razync")
_ALLOWED_FIELDS = {
    "page", "operation", "backend", "duration_ms", "status", "error_type",
    "feature", "count", "source", "environment",
}


def safe_event(event: str, *, level: str = "info", **fields) -> None:
    """Emit structured operational logs without PII, tokens or document contents."""
    payload = {
        "event": str(event)[:80],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for key, value in fields.items():
        if key in _ALLOWED_FIELDS and value is not None:
            payload[key] = str(value)[:160]
    message = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    log_method = getattr(_logger, level if level in {"debug", "info", "warning", "error", "critical"} else "info")
    log_method(message)


def safe_error(event: str, exc: Exception, **fields) -> None:
    safe_event(event, level="error", error_type=type(exc).__name__, status="error", **fields)
