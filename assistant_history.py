from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import DATABASE_URL, engine
from monitoring import safe_error


class AssistantHistoryError(RuntimeError):
    """Safe error raised when assistant history is temporarily unavailable."""


WELCOME_MESSAGE = (
    "Olá! Como posso ajudar? Posso analisar seu negócio ou preparar receitas, "
    "despesas e notas para sua confirmação."
)


def _is_sqlite() -> bool:
    return str(DATABASE_URL).startswith("sqlite")


def _ensure_sqlite_tables() -> None:
    if not _is_sqlite():
        return
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(120) NOT NULL DEFAULT 'Nova conversa',
                channel VARCHAR(20) NOT NULL DEFAULT 'web',
                archived BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ai_conversations_user_updated
            ON ai_conversations (user_id, updated_at DESC)
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                metadata_json TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ai_messages_conversation_created
            ON ai_messages (conversation_id, created_at, id)
        """))


def _safe_title(value: str) -> str:
    compact = " ".join(str(value or "").split())
    return (compact[:74] + "…") if len(compact) > 75 else (compact or "Nova conversa")


def create_conversation(user_id: int, *, channel: str = "web", title: str = "Nova conversa") -> int:
    try:
        _ensure_sqlite_tables()
        with engine.begin() as conn:
            conversation_id = conn.execute(
                text("""
                    INSERT INTO ai_conversations (user_id, title, channel, archived, created_at, updated_at)
                    VALUES (:uid, :title, :channel, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """),
                {"uid": int(user_id), "title": _safe_title(title), "channel": str(channel or "web")[:20]},
            ).scalar_one()
        return int(conversation_id)
    except SQLAlchemyError as exc:
        safe_error("assistant_history_create_failed", exc, feature="assistant_history", operation="create")
        raise AssistantHistoryError("Não foi possível iniciar uma nova conversa agora.") from exc


def conversation_belongs_to_user(user_id: int, conversation_id: int) -> bool:
    try:
        _ensure_sqlite_tables()
        with engine.connect() as conn:
            value = conn.execute(
                text("SELECT 1 FROM ai_conversations WHERE id = :cid AND user_id = :uid AND archived = false"),
                {"cid": int(conversation_id), "uid": int(user_id)},
            ).scalar_one_or_none()
        return bool(value)
    except SQLAlchemyError as exc:
        safe_error("assistant_history_validate_failed", exc, feature="assistant_history", operation="validate")
        raise AssistantHistoryError("Não foi possível validar esta conversa.") from exc


def get_or_create_conversation(user_id: int, conversation_id: int | None = None) -> int:
    if conversation_id is not None and conversation_belongs_to_user(user_id, conversation_id):
        return int(conversation_id)
    conversations = list_conversations(user_id, limit=1)
    if conversations:
        return int(conversations[0]["id"])
    return create_conversation(user_id)


def list_conversations(user_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 50))
    try:
        _ensure_sqlite_tables()
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT id, title, channel, created_at, updated_at
                    FROM ai_conversations
                    WHERE user_id = :uid AND archived = false
                    ORDER BY updated_at DESC, id DESC
                    LIMIT :limit
                """),
                {"uid": int(user_id), "limit": safe_limit},
            ).mappings().all()
        return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        safe_error("assistant_history_list_failed", exc, feature="assistant_history", operation="list")
        raise AssistantHistoryError("Não foi possível carregar suas conversas.") from exc


def load_messages(user_id: int, conversation_id: int, *, limit: int = 200) -> list[dict[str, str]]:
    safe_limit = max(1, min(int(limit), 500))
    try:
        _ensure_sqlite_tables()
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT role, content FROM (
                        SELECT id, role, content, created_at
                        FROM ai_messages
                        WHERE conversation_id = :cid AND user_id = :uid
                        ORDER BY created_at DESC, id DESC
                        LIMIT :limit
                    ) recent
                    ORDER BY created_at ASC, id ASC
                """),
                {"cid": int(conversation_id), "uid": int(user_id), "limit": safe_limit},
            ).mappings().all()
        return [{"role": str(row["role"]), "content": str(row["content"])} for row in rows]
    except SQLAlchemyError as exc:
        safe_error("assistant_history_load_failed", exc, feature="assistant_history", operation="load")
        raise AssistantHistoryError("Não foi possível carregar o histórico da conversa.") from exc


def append_message(
    user_id: int,
    conversation_id: int,
    role: str,
    content: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    safe_role = str(role).strip().lower()
    if safe_role not in {"user", "assistant", "system"}:
        raise ValueError("Papel de mensagem inválido.")
    safe_content = str(content or "").strip()
    if not safe_content:
        return
    safe_content = safe_content[:16000]
    metadata_json = json.dumps(metadata, ensure_ascii=False, default=str)[:8000] if metadata else None
    try:
        _ensure_sqlite_tables()
        with engine.begin() as conn:
            owned = conn.execute(
                text("SELECT title FROM ai_conversations WHERE id = :cid AND user_id = :uid AND archived = false"),
                {"cid": int(conversation_id), "uid": int(user_id)},
            ).scalar_one_or_none()
            if owned is None:
                raise AssistantHistoryError("Esta conversa não está disponível para sua conta.")
            conn.execute(
                text("""
                    INSERT INTO ai_messages (conversation_id, user_id, role, content, metadata_json, created_at)
                    VALUES (:cid, :uid, :role, :content, :metadata, CURRENT_TIMESTAMP)
                """),
                {"cid": int(conversation_id), "uid": int(user_id), "role": safe_role, "content": safe_content, "metadata": metadata_json},
            )
            values: dict[str, Any] = {"cid": int(conversation_id), "uid": int(user_id)}
            title_sql = ""
            if safe_role == "user" and str(owned) == "Nova conversa":
                values["title"] = _safe_title(safe_content)
                title_sql = ", title = :title"
            conn.execute(
                text(f"UPDATE ai_conversations SET updated_at = CURRENT_TIMESTAMP{title_sql} WHERE id = :cid AND user_id = :uid"),
                values,
            )
    except AssistantHistoryError:
        raise
    except SQLAlchemyError as exc:
        safe_error("assistant_history_append_failed", exc, feature="assistant_history", operation="append")
        raise AssistantHistoryError("A mensagem não pôde ser salva no histórico.") from exc


def archive_conversation(user_id: int, conversation_id: int) -> None:
    try:
        _ensure_sqlite_tables()
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE ai_conversations SET archived = true, updated_at = CURRENT_TIMESTAMP WHERE id = :cid AND user_id = :uid"),
                {"cid": int(conversation_id), "uid": int(user_id)},
            )
    except SQLAlchemyError as exc:
        safe_error("assistant_history_archive_failed", exc, feature="assistant_history", operation="archive")
        raise AssistantHistoryError("Não foi possível arquivar esta conversa.") from exc


def serialize_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return str(value or "")

