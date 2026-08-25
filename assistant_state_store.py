from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from database import DATABASE_URL, engine


class AssistantStateStoreError(RuntimeError):
    """Erro seguro ao persistir rascunhos ou avaliações da IA."""


def _ensure_sqlite_tables() -> None:
    if not str(DATABASE_URL).startswith("sqlite"):
        return
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_action_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action_key VARCHAR(64) NOT NULL,
                conversation_id INTEGER,
                channel VARCHAR(20) NOT NULL DEFAULT 'web',
                action_type VARCHAR(40) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                summary VARCHAR(500) NOT NULL DEFAULT '',
                draft_json TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, action_key)
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ai_action_drafts_user_status
            ON ai_action_drafts (user_id, status, updated_at DESC)
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conversation_id INTEGER,
                message_key VARCHAR(64) NOT NULL,
                helpful BOOLEAN NOT NULL,
                note VARCHAR(500) NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, message_key)
            )
        """))


def _json_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or ""))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def save_draft(user_id: int, draft: dict[str, Any], *, conversation_id: int | None = None) -> None:
    _ensure_sqlite_tables()
    action_key = str(draft.get("action_key") or "")[:64]
    if not action_key:
        return
    values = {
        "uid": int(user_id), "key": action_key,
        "conversation_id": int(conversation_id) if conversation_id else None,
        "channel": "whatsapp" if str(draft.get("channel") or "").lower() == "whatsapp" else "web",
        "action_type": str(draft.get("action_type") or "")[:40],
        "summary": str(draft.get("summary") or "")[:500],
        "draft": json.dumps(draft, ensure_ascii=False, default=str),
    }
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO ai_action_drafts
                    (user_id, action_key, conversation_id, channel, action_type, status, summary, draft_json, created_at, updated_at)
                VALUES (:uid, :key, :conversation_id, :channel, :action_type, 'pending', :summary, :draft,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, action_key) DO UPDATE SET
                    conversation_id = EXCLUDED.conversation_id,
                    summary = EXCLUDED.summary,
                    draft_json = EXCLUDED.draft_json,
                    status = 'pending',
                    updated_at = CURRENT_TIMESTAMP
            """), values)
    except Exception as exc:
        raise AssistantStateStoreError("Não foi possível guardar a ação preparada.") from exc


def set_draft_status(user_id: int, action_key: str, status: str) -> None:
    if status not in {"pending", "confirmed", "cancelled"} or not action_key:
        return
    _ensure_sqlite_tables()
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE ai_action_drafts SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :uid AND action_key = :key
            """), {"uid": int(user_id), "key": str(action_key)[:64], "status": status})
    except Exception as exc:
        raise AssistantStateStoreError("Não foi possível atualizar o estado da aprovação.") from exc


def list_pending_drafts(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    _ensure_sqlite_tables()
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT action_key, conversation_id, channel, action_type, summary, draft_json, created_at, updated_at
                FROM ai_action_drafts
                WHERE user_id = :uid AND status = 'pending'
                ORDER BY updated_at DESC, id DESC LIMIT :limit
            """), {"uid": int(user_id), "limit": max(1, min(int(limit), 100))}).mappings().all()
    except Exception as exc:
        raise AssistantStateStoreError("Não foi possível carregar as aprovações pendentes.") from exc
    result: list[dict[str, Any]] = []
    for row in rows:
        draft = _json_dict(row.get("draft_json"))
        if not draft:
            continue
        draft["conversation_id"] = row.get("conversation_id")
        for key in ("created_at", "updated_at"):
            value = row.get(key)
            draft[key] = value.isoformat() if isinstance(value, datetime) else str(value or "")
        result.append(draft)
    return result


def message_key(content: str) -> str:
    return hashlib.sha256(str(content or "").strip().encode("utf-8")).hexdigest()[:32]


def save_feedback(
    user_id: int,
    content: str,
    helpful: bool,
    *,
    conversation_id: int | None = None,
    note: str = "",
) -> None:
    _ensure_sqlite_tables()
    values = {
        "uid": int(user_id), "conversation_id": int(conversation_id) if conversation_id else None,
        "message_key": message_key(content), "helpful": bool(helpful), "note": str(note)[:500],
    }
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO ai_feedback (user_id, conversation_id, message_key, helpful, note, created_at)
                VALUES (:uid, :conversation_id, :message_key, :helpful, :note, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, message_key) DO UPDATE SET
                    helpful = EXCLUDED.helpful, note = EXCLUDED.note,
                    conversation_id = EXCLUDED.conversation_id
            """), values)
    except Exception as exc:
        raise AssistantStateStoreError("Não foi possível registrar sua avaliação.") from exc
