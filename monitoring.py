from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

_logger = logging.getLogger("razync")
_ALLOWED_FIELDS = {
    "page", "operation", "backend", "duration_ms", "status", "error_type",
    "feature", "count", "source", "environment",
}
_SENTRY_INITIALIZED = False


def _secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def observability_configured() -> bool:
    return bool(_secret("SENTRY_DSN"))


def _scrub_sentry_event(event: dict, hint: dict) -> dict:
    """Keep operational exception metadata while removing user/request payloads."""
    event.pop("request", None)
    event.pop("user", None)
    event.pop("breadcrumbs", None)
    event.pop("extra", None)
    contexts = event.get("contexts")
    if isinstance(contexts, dict):
        event["contexts"] = {
            key: value for key, value in contexts.items()
            if key in {"runtime", "os", "trace"}
        }
    return event


def configure_observability() -> bool:
    global _SENTRY_INITIALIZED
    if _SENTRY_INITIALIZED:
        return True
    dsn = _secret("SENTRY_DSN")
    if not dsn:
        return False
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            environment=_secret("APP_ENVIRONMENT") or "production",
            release=_secret("APP_RELEASE") or None,
            send_default_pii=False,
            traces_sample_rate=0.05,
            profiles_sample_rate=0.0,
            before_send=_scrub_sentry_event,
        )
    except Exception as exc:
        _logger.warning("Sentry initialization failed: %s", type(exc).__name__)
        return False
    _SENTRY_INITIALIZED = True
    return True


def safe_event(event: str, *, level: str = "info", **fields) -> None:
    """Emit structured operational logs without PII, tokens or document contents."""
    configure_observability()
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

    if _SENTRY_INITIALIZED and level in {"warning", "error", "critical"}:
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                for key, value in payload.items():
                    if key not in {"event", "timestamp"}:
                        scope.set_tag(key, value)
                sentry_sdk.capture_message(payload["event"], level=level)
        except Exception:
            pass


def safe_error(event: str, exc: Exception, **fields) -> None:
    safe_event(event, level="error", error_type=type(exc).__name__, status="error", **fields)
    if _SENTRY_INITIALIZED:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
