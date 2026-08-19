from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import DATABASE_URL, engine


class AIUsageStoreError(RuntimeError):
    """Safe error raised when AI usage persistence is unavailable."""


def utc_usage_date() -> date:
    return datetime.now(timezone.utc).date()


def _is_sqlite() -> bool:
    return str(DATABASE_URL).startswith("sqlite")


def _ensure_sqlite_table() -> None:
    if not _is_sqlite():
        return
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_daily_usage (
                user_id INTEGER NOT NULL,
                usage_date DATE NOT NULL,
                request_count INTEGER NOT NULL DEFAULT 0 CHECK (request_count >= 0),
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, usage_date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))


def get_ai_usage(user_id: int, usage_date: date | None = None) -> int:
    day = usage_date or utc_usage_date()
    try:
        _ensure_sqlite_table()
        with engine.connect() as conn:
            value = conn.execute(
                text("""
                    SELECT request_count
                    FROM ai_daily_usage
                    WHERE user_id = :uid AND usage_date = :usage_date
                """),
                {"uid": int(user_id), "usage_date": day},
            ).scalar_one_or_none()
        return int(value or 0)
    except SQLAlchemyError as exc:
        raise AIUsageStoreError("Não foi possível consultar o limite diário da IA.") from exc


def reserve_ai_request(user_id: int, daily_limit: int, usage_date: date | None = None) -> tuple[bool, int]:
    """Atomically reserve one request. Returns (allowed, resulting_count)."""
    limit = max(1, int(daily_limit))
    day = usage_date or utc_usage_date()
    try:
        _ensure_sqlite_table()
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    INSERT INTO ai_daily_usage (user_id, usage_date, request_count, updated_at)
                    VALUES (:uid, :usage_date, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, usage_date) DO UPDATE
                    SET request_count = ai_daily_usage.request_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ai_daily_usage.request_count < :daily_limit
                    RETURNING request_count
                """),
                {"uid": int(user_id), "usage_date": day, "daily_limit": limit},
            ).scalar_one_or_none()
        if row is None:
            return False, get_ai_usage(user_id, day)
        return True, int(row)
    except SQLAlchemyError as exc:
        raise AIUsageStoreError("Não foi possível reservar o uso diário da IA.") from exc


def release_ai_request(user_id: int, usage_date: date | None = None) -> int:
    """Refund a reservation when the provider call fails."""
    day = usage_date or utc_usage_date()
    try:
        _ensure_sqlite_table()
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    UPDATE ai_daily_usage
                    SET request_count = CASE WHEN request_count > 0 THEN request_count - 1 ELSE 0 END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :uid AND usage_date = :usage_date
                    RETURNING request_count
                """),
                {"uid": int(user_id), "usage_date": day},
            ).scalar_one_or_none()
        return int(row or 0)
    except SQLAlchemyError as exc:
        raise AIUsageStoreError("Não foi possível devolver a reserva da IA.") from exc
