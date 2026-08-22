from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import DATABASE_URL, engine


class AssistantActionStoreError(RuntimeError):
    """Erro seguro ao registrar a execução de uma automação."""


def _ensure_sqlite_table() -> None:
    if not str(DATABASE_URL).startswith("sqlite"):
        return
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_action_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action_key VARCHAR(64) NOT NULL,
                action_type VARCHAR(40) NOT NULL,
                channel VARCHAR(20) NOT NULL DEFAULT 'web',
                status VARCHAR(20) NOT NULL DEFAULT 'processing',
                summary VARCHAR(500) NOT NULL DEFAULT '',
                receipt_json TEXT,
                error_message VARCHAR(500),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, action_key)
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ai_action_executions_user_created
            ON ai_action_executions (user_id, created_at DESC)
        """))


def _decode_receipt(value: Any) -> dict[str, Any] | None:
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def claim_action(
    user_id: int,
    action_key: str,
    *,
    action_type: str,
    channel: str,
    summary: str,
) -> tuple[bool, dict[str, Any] | None]:
    """Reserva uma chave uma única vez e devolve recibo anterior, se existir."""
    _ensure_sqlite_table()
    values = {
        "uid": int(user_id),
        "key": str(action_key)[:64],
        "type": str(action_type)[:40],
        "channel": "whatsapp" if str(channel).lower() == "whatsapp" else "web",
        "summary": str(summary)[:500],
    }
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO ai_action_executions
                    (user_id, action_key, action_type, channel, status, summary, created_at, updated_at)
                VALUES (:uid, :key, :type, :channel, 'processing', :summary, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), values)
        return True, None
    except IntegrityError:
        pass
    except Exception as exc:
        raise AssistantActionStoreError("Não foi possível proteger esta ação contra duplicidade.") from exc

    try:
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT status, receipt_json
                FROM ai_action_executions
                WHERE user_id = :uid AND action_key = :key
            """), values).mappings().first()
            if row and row["status"] == "failed":
                updated = conn.execute(text("""
                    UPDATE ai_action_executions
                    SET status = 'processing', error_message = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :uid AND action_key = :key AND status = 'failed'
                """), values)
                if updated.rowcount:
                    return True, None
    except Exception as exc:
        raise AssistantActionStoreError("Não foi possível consultar o estado desta ação.") from exc
    return False, _decode_receipt(row["receipt_json"]) if row else None


def complete_action(user_id: int, action_key: str, receipt: dict[str, Any]) -> None:
    _ensure_sqlite_table()
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE ai_action_executions
                SET status = 'completed', receipt_json = :receipt, error_message = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :uid AND action_key = :key
            """), {
                "uid": int(user_id), "key": str(action_key)[:64],
                "receipt": json.dumps(receipt, ensure_ascii=False, default=str),
            })
    except Exception as exc:
        raise AssistantActionStoreError("A ação foi salva, mas o recibo não pôde ser registrado.") from exc


def fail_action(user_id: int, action_key: str, message: str) -> None:
    _ensure_sqlite_table()
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE ai_action_executions
                SET status = 'failed', error_message = :message, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :uid AND action_key = :key
            """), {"uid": int(user_id), "key": str(action_key)[:64], "message": str(message)[:500]})
    except Exception:
        return


def mark_action_undone(user_id: int, action_key: str) -> None:
    if not action_key:
        return
    _ensure_sqlite_table()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE ai_action_executions
            SET status = 'undone', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :uid AND action_key = :key
        """), {"uid": int(user_id), "key": str(action_key)[:64]})


def list_actions(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    _ensure_sqlite_table()
    safe_limit = max(1, min(int(limit), 100))
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT action_key, action_type, channel, status, summary, receipt_json, created_at, updated_at
                FROM ai_action_executions
                WHERE user_id = :uid
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
            """), {"uid": int(user_id), "limit": safe_limit}).mappings().all()
    except Exception as exc:
        raise AssistantActionStoreError("Não foi possível carregar o histórico de ações da IA.") from exc
    result = []
    for row in rows:
        item = dict(row)
        item["receipt"] = _decode_receipt(item.pop("receipt_json", None))
        for key in ("created_at", "updated_at"):
            if isinstance(item.get(key), datetime):
                item[key] = item[key].isoformat()
        result.append(item)
    return result

