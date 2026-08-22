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


class ProductionConfigurationError(RuntimeError):
    """Raised when production would otherwise start with an unsafe fallback."""


def _secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def is_production_environment() -> bool:
    return (_secret("APP_ENVIRONMENT") or "").strip().lower() in {"production", "prod"}


def validate_production_configuration() -> None:
    """Prevent production from silently falling back to SQLite or legacy auth.

    Development remains permissive. In production the server must receive explicit
    PostgreSQL/Supabase, Auth and session-persistence configuration.
    """
    if not is_production_environment():
        return

    missing: list[str] = []
    database_url = _secret("DATABASE_URL")
    has_postgres_url = database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://"))
    has_pooler = bool(_secret("SUPABASE_DB_PASSWORD") and _secret("SUPABASE_DB_HOST") and _secret("SUPABASE_DB_USER"))
    if not (has_postgres_url or has_pooler):
        missing.append("PostgreSQL/Supabase Database")

    if not _secret("SUPABASE_URL"):
        missing.append("SUPABASE_URL")
    if not _secret("SUPABASE_PUBLISHABLE_KEY"):
        missing.append("SUPABASE_PUBLISHABLE_KEY")
    session_secret = _secret("SESSION_COOKIE_SECRET")
    if len(session_secret) < 32:
        missing.append("SESSION_COOKIE_SECRET (32+ caracteres)")

    if missing:
        raise ProductionConfigurationError(
            "Configuração de produção incompleta. O Razync recusou iniciar em modo de fallback: "
            + ", ".join(missing)
            + "."
        )


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


# Import-time guard is intentional: app.py imports this module before init_db().
# In production, unsafe fallbacks are rejected before any business data is loaded.
validate_production_configuration()
