from __future__ import annotations

import hashlib
import hmac
import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, LargeBinary,
    MetaData, String, Table, Text, create_engine, delete, insert, select, update
)
from sqlalchemy.exc import IntegrityError

def _resolve_database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if not configured:
        try:
            import streamlit as st
            configured = str(st.secrets.get("DATABASE_URL", "")).strip()
        except Exception:
            configured = ""
    if configured:
        if configured.startswith("postgres://"):
            configured = "postgresql+psycopg://" + configured[len("postgres://"):]
        elif configured.startswith("postgresql://") and "+psycopg" not in configured:
            configured = "postgresql+psycopg://" + configured[len("postgresql://"):]
        return configured
    fallback = Path(tempfile.gettempdir()) / "razync_pro.db"
    return f"sqlite:///{fallback.as_posix()}"


DATABASE_URL = _resolve_database_url()

engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, future=True, **engine_kwargs)
metadata = MetaData()


def database_runtime_info() -> dict[str, Any]:
    is_sqlite = DATABASE_URL.startswith("sqlite")
    return {
        "backend": "SQLite temporário" if is_sqlite else "PostgreSQL",
        "persistent": not is_sqlite,
        "production_ready": not is_sqlite,
    }

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(120), nullable=False),
    Column("email", String(255), nullable=False, unique=True, index=True),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

profiles = Table(
    "mei_profiles", metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("business_name", String(180), default=""),
    Column("trade_name", String(180), default=""),
    Column("cnpj", String(30), default=""),
    Column("main_activity", String(255), default=""),
    Column("activity_type", String(40), default="Serviços"),
    Column("opening_date", Date, nullable=True),
    Column("annual_limit", Float, nullable=False, default=81000.0),
    Column("phone", String(40), default=""),
    Column("city", String(120), default=""),
    Column("state", String(2), default=""),
    Column("municipal_registration", String(80), default=""),
    Column("state_registration", String(80), default=""),
    Column("has_employee", Boolean, nullable=False, default=False),
)

transactions = Table(
    "transactions", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("tx_date", Date, nullable=False),
    Column("tx_type", String(20), nullable=False),
    Column("description", String(255), nullable=False),
    Column("category", String(100), nullable=False),
    Column("value", Float, nullable=False),
    Column("document_number", String(100), default=""),
    Column("counterparty", String(180), default=""),
    Column("payment_method", String(80), default=""),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

das_items = Table(
    "das_items", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("competence", String(7), nullable=False),
    Column("due_date", Date, nullable=True),
    Column("amount", Float, nullable=False, default=0),
    Column("status", String(30), nullable=False, default="Pendente"),
    Column("payment_date", Date, nullable=True),
    Column("notes", Text, default=""),
)

documents = Table(
    "documents", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("filename", String(255), nullable=False),
    Column("mime_type", String(120), default=""),
    Column("content", LargeBinary, nullable=False),
    Column("category", String(100), default="Outros"),
    Column("reference_month", String(7), default=""),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

invoices = Table(
    "invoices", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("issue_date", Date, nullable=False),
    Column("invoice_type", String(30), nullable=False, default="Serviço"),
    Column("number", String(100), default=""),
    Column("customer", String(180), default=""),
    Column("customer_document", String(30), default=""),
    Column("description", String(255), default=""),
    Column("amount", Float, nullable=False, default=0),
    Column("status", String(30), default="Emitida"),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

contacts = Table(
    "contacts", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("contact_type", String(30), nullable=False),
    Column("name", String(180), nullable=False),
    Column("document", String(30), default=""),
    Column("email", String(255), default=""),
    Column("phone", String(40), default=""),
    Column("notes", Text, default=""),
)

employees = Table(
    "employees", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("name", String(180), nullable=False),
    Column("cpf", String(30), default=""),
    Column("admission_date", Date, nullable=True),
    Column("salary", Float, nullable=False, default=0),
    Column("status", String(30), default="Ativo"),
    Column("notes", Text, default=""),
)

obligations = Table(
    "obligations", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("title", String(180), nullable=False),
    Column("due_date", Date, nullable=True),
    Column("status", String(30), default="Pendente"),
    Column("category", String(80), default="Fiscal"),
    Column("notes", Text, default=""),
)

def init_db() -> None:
    metadata.create_all(engine)

def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"{salt.hex()}:{digest.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 240_000)
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except Exception:
        return False

def create_user(name: str, email: str, password: str) -> tuple[bool, str]:
    try:
        with engine.begin() as conn:
            result = conn.execute(insert(users).values(name=name.strip(), email=email.strip().lower(), password_hash=_hash_password(password)))
            uid = int(result.inserted_primary_key[0])
            conn.execute(insert(profiles).values(user_id=uid))
        return True, "Conta criada com sucesso."
    except IntegrityError:
        return False, "Já existe uma conta com este e-mail."

def authenticate(email: str, password: str) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.email == email.strip().lower())).mappings().first()
    if not row or not _verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}

def get_profile(user_id: int) -> dict[str, Any]:
    with engine.connect() as conn:
        row = conn.execute(select(users.c.name, users.c.email, profiles).join(profiles, profiles.c.user_id == users.c.id).where(users.c.id == user_id)).mappings().first()
    return dict(row) if row else {}

def save_profile(user_id: int, **data: Any) -> None:
    allowed = {c.name for c in profiles.c if c.name != "user_id"}
    payload = {k: v for k, v in data.items() if k in allowed}
    with engine.begin() as conn:
        existing = conn.execute(select(profiles.c.user_id).where(profiles.c.user_id == user_id)).first()
        if existing:
            conn.execute(update(profiles).where(profiles.c.user_id == user_id).values(**payload))
        else:
            conn.execute(insert(profiles).values(user_id=user_id, **payload))

def add_transaction(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(transactions).values(user_id=user_id, **data))

def list_transactions(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc())).mappings().all()
    return [dict(r) for r in rows]

def delete_transaction(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(transactions).where(transactions.c.user_id == user_id, transactions.c.id == item_id))


def link_transaction_document(user_id: int, item_id: int, document_number: str, counterparty: str = "") -> None:
    payload = {"document_number": (document_number or "").strip()}
    if counterparty:
        payload["counterparty"] = counterparty.strip()
    with engine.begin() as conn:
        conn.execute(update(transactions).where(transactions.c.user_id == user_id, transactions.c.id == item_id).values(**payload))

def upsert_das(user_id: int, competence: str, due_date, amount: float, status: str, payment_date, notes: str) -> None:
    with engine.begin() as conn:
        row = conn.execute(select(das_items.c.id).where(das_items.c.user_id == user_id, das_items.c.competence == competence)).first()
        payload = dict(due_date=due_date, amount=amount, status=status, payment_date=payment_date, notes=notes)
        if row:
            conn.execute(update(das_items).where(das_items.c.id == row[0]).values(**payload))
        else:
            conn.execute(insert(das_items).values(user_id=user_id, competence=competence, **payload))

def list_das(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(das_items).where(das_items.c.user_id == user_id).order_by(das_items.c.competence.desc())).mappings().all()
    return [dict(r) for r in rows]

def save_document(user_id: int, filename: str, mime_type: str, content: bytes, category: str, reference_month: str = "") -> None:
    with engine.begin() as conn:
        conn.execute(insert(documents).values(user_id=user_id, filename=filename, mime_type=mime_type, content=content, category=category, reference_month=reference_month))

def list_documents(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(documents.c.id, documents.c.filename, documents.c.mime_type, documents.c.category, documents.c.reference_month, documents.c.created_at).where(documents.c.user_id == user_id).order_by(documents.c.id.desc())).mappings().all()
    return [dict(r) for r in rows]

def get_document(user_id: int, item_id: int) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(select(documents).where(documents.c.user_id == user_id, documents.c.id == item_id)).mappings().first()
    return dict(row) if row else None

def delete_document(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(documents).where(documents.c.user_id == user_id, documents.c.id == item_id))

def add_invoice(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(invoices).values(user_id=user_id, **data))

def list_invoices(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(invoices).where(invoices.c.user_id == user_id).order_by(invoices.c.issue_date.desc(), invoices.c.id.desc())).mappings().all()
    return [dict(r) for r in rows]

def delete_invoice(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(invoices).where(invoices.c.user_id == user_id, invoices.c.id == item_id))

def add_contact(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(contacts).values(user_id=user_id, **data))

def list_contacts(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(contacts).where(contacts.c.user_id == user_id).order_by(contacts.c.name)).mappings().all()
    return [dict(r) for r in rows]

def delete_contact(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(contacts).where(contacts.c.user_id == user_id, contacts.c.id == item_id))

def add_employee(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(employees).values(user_id=user_id, **data))
        conn.execute(update(profiles).where(profiles.c.user_id == user_id).values(has_employee=True))

def list_employees(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(employees).where(employees.c.user_id == user_id).order_by(employees.c.id.desc())).mappings().all()
    return [dict(r) for r in rows]

def delete_employee(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(employees).where(employees.c.user_id == user_id, employees.c.id == item_id))
        active_count = conn.execute(select(employees.c.id).where(employees.c.user_id == user_id, employees.c.status == "Ativo")).all()
        conn.execute(update(profiles).where(profiles.c.user_id == user_id).values(has_employee=bool(active_count)))

def add_obligation(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(obligations).values(user_id=user_id, **data))

def list_obligations(user_id: int) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(select(obligations).where(obligations.c.user_id == user_id).order_by(obligations.c.due_date)).mappings().all()
    return [dict(r) for r in rows]

def update_obligation_status(user_id: int, item_id: int, status: str) -> None:
    with engine.begin() as conn:
        conn.execute(update(obligations).where(obligations.c.user_id == user_id, obligations.c.id == item_id).values(status=status))

def delete_obligation(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(obligations).where(obligations.c.user_id == user_id, obligations.c.id == item_id))
