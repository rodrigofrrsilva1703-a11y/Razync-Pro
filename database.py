from __future__ import annotations

import hashlib
import hmac
import os
import tempfile
import time
import copy
import json
from functools import lru_cache
from pathlib import Path
from datetime import datetime, date
from typing import Any

from automation_tools import next_recurrence_date

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, Numeric, Uuid,
    MetaData, String, Table, Text, create_engine, delete, insert, select, update, func, case, extract, text
)
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.engine import URL


class DatabaseConnectionError(RuntimeError):
    """Safe database error that never exposes credentials."""


def _secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def _resolve_database_url():
    password = _secret("SUPABASE_DB_PASSWORD")
    if password:
        host = _secret("SUPABASE_DB_HOST") or "aws-0-sa-east-1.pooler.supabase.com"
        user = _secret("SUPABASE_DB_USER") or "postgres.etimfgenlludorrftapb"
        port_raw = _secret("SUPABASE_DB_PORT") or "5432"
        try:
            port = int(port_raw)
        except ValueError:
            port = 5432
        return URL.create(
            drivername="postgresql+psycopg",
            username=user,
            password=password,
            host=host,
            port=port,
            database="postgres",
            query={"sslmode": "require"},
        )

    configured = _secret("DATABASE_URL")
    if configured:
        if configured.startswith("postgres://"):
            configured = "postgresql+psycopg://" + configured[len("postgres://"):]
        elif configured.startswith("postgresql://") and "+psycopg" not in configured:
            configured = "postgresql+psycopg://" + configured[len("postgresql://"):]
        return configured

    fallback = Path(tempfile.gettempdir()) / "razync_pro.db"
    return f"sqlite:///{fallback.as_posix()}"


def _diagnose_operational_error(exc: Exception) -> str:
    raw = str(getattr(exc, "orig", exc)).lower()
    if "password authentication failed" in raw or "authentication failed" in raw:
        return "A senha do banco foi recusada pelo Supabase. Redefina a Database Password e atualize SUPABASE_DB_PASSWORD nos Secrets do Streamlit."
    if "tenant or user not found" in raw or "user not found" in raw:
        return "O usuário do Session Pooler não foi reconhecido. Confira SUPABASE_DB_USER e o Project Ref do Razync Pro."
    if "could not translate host name" in raw or "name or service not known" in raw or "nodename nor servname" in raw:
        return "O endereço do Session Pooler não pôde ser resolvido. Confira SUPABASE_DB_HOST no Streamlit Secrets."
    if "timeout" in raw or "timed out" in raw:
        return "A conexão com o Supabase expirou. O host/porta do pooler pode estar incorreto ou temporariamente indisponível."
    if "connection refused" in raw:
        return "O servidor recusou a conexão. Confira o host e a porta do Session Pooler."
    if "ssl" in raw or "certificate" in raw:
        return "Falha na conexão SSL com o Supabase. O Razync exige SSL para o banco de produção."
    if "too many connections" in raw or "max clients" in raw:
        return "O pool de conexões do Supabase atingiu o limite. Aguarde alguns instantes e reinicie o app."
    if "server closed the connection" in raw or "connection reset" in raw:
        return "O Supabase encerrou a conexão durante a abertura. Reinicie o app e tente novamente."
    return "Não foi possível abrir a conexão com o PostgreSQL. Confira senha, host, usuário e porta do Session Pooler nos Secrets do Streamlit."


DATABASE_URL = _resolve_database_url()

engine_kwargs: dict[str, Any] = {"pool_pre_ping": False}
if str(DATABASE_URL).startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["connect_args"] = {"connect_timeout": 8}
    engine_kwargs.update({
        "pool_size": 3,
        "max_overflow": 2,
        "pool_recycle": 1800,
        "pool_timeout": 10,
        "pool_use_lifo": True,
    })

engine = create_engine(DATABASE_URL, future=True, **engine_kwargs)
metadata = MetaData()


def database_runtime_info() -> dict[str, Any]:
    is_sqlite = str(DATABASE_URL).startswith("sqlite")
    return {
        "backend": "SQLite temporário" if is_sqlite else "PostgreSQL / Supabase",
        "persistent": not is_sqlite,
        "production_ready": not is_sqlite,
        "host": "local temporário" if is_sqlite else (_secret("SUPABASE_DB_HOST") or "Session Pooler Supabase"),
    }

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(120), nullable=False),
    Column("email", String(255), nullable=False, unique=True, index=True),
    Column("auth_user_id", Uuid(as_uuid=False), nullable=True, unique=True, index=True),
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
    Column("annual_limit", Numeric(14, 2), nullable=False, default=81000.0),
    Column("phone", String(40), default=""),
    Column("city", String(120), default=""),
    Column("state", String(2), default=""),
    Column("municipal_registration", String(80), default=""),
    Column("state_registration", String(80), default=""),
    Column("has_employee", Boolean, nullable=False, default=False),
)

recurring_transactions = Table(
    "recurring_transactions", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("tx_type", String(20), nullable=False),
    Column("description", String(255), nullable=False),
    Column("category", String(100), nullable=False, default="Outros"),
    Column("value", Numeric(14, 2), nullable=False),
    Column("payment_method", String(80), nullable=False, default="Outro"),
    Column("frequency", String(20), nullable=False),
    Column("next_date", Date, nullable=False),
    Column("end_date", Date, nullable=True),
    Column("active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

transactions = Table(
    "transactions", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("tx_date", Date, nullable=False),
    Column("tx_type", String(20), nullable=False),
    Column("description", String(255), nullable=False),
    Column("category", String(100), nullable=False),
    Column("value", Numeric(14, 2), nullable=False),
    Column("document_number", String(100), default=""),
    Column("counterparty", String(180), default=""),
    Column("payment_method", String(80), default=""),
    Column("recurring_transaction_id", Integer, ForeignKey("recurring_transactions.id", ondelete="SET NULL"), nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)

das_items = Table(
    "das_items", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("competence", String(7), nullable=False),
    Column("due_date", Date, nullable=True),
    Column("amount", Numeric(14, 2), nullable=False, default=0),
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
    Column("content", LargeBinary, nullable=True),
    Column("storage_path", Text, nullable=True),
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
    Column("amount", Numeric(14, 2), nullable=False, default=0),
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
    Column("salary", Numeric(14, 2), nullable=False, default=0),
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


_USER_VERSION: dict[int, int] = {}
_READ_CACHE: dict[tuple[str, int], tuple[float, Any]] = {}
_READ_CACHE_TTL = 30.0
_RECURRING_MATERIALIZE_CHECK: dict[int, date] = {}

def _cache_get(domain: str, user_id: int):
    key = (domain, int(user_id))
    item = _READ_CACHE.get(key)
    if not item:
        return None
    created, value = item
    if time.monotonic() - created > _READ_CACHE_TTL:
        _READ_CACHE.pop(key, None)
        return None
    return copy.deepcopy(value)

def _cache_set(domain: str, user_id: int, value):
    _READ_CACHE[(domain, int(user_id))] = (time.monotonic(), copy.deepcopy(value))
    return copy.deepcopy(value)

def _cache_invalidate(domain: str, user_id: int) -> None:
    uid = int(user_id)
    _READ_CACHE.pop((domain, uid), None)
    _USER_VERSION[uid] = _USER_VERSION.get(uid, 0) + 1

def data_version(user_id: int) -> int:
    return _USER_VERSION.get(int(user_id), 0)



@lru_cache(maxsize=1)
def init_db() -> None:
    if not str(DATABASE_URL).startswith("sqlite"):
        return
    try:
        metadata.create_all(engine)
    except OperationalError as exc:
        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None


def _snapshot_date(value):
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return value
    return value


def load_user_snapshot(user_id: int) -> dict[str, Any]:
    if str(DATABASE_URL).startswith("sqlite"):
        return {
            "profile": get_profile(user_id),
            "transactions": list_transactions(user_id),
            "invoices": list_invoices(user_id),
            "das": list_das(user_id),
            "documents": list_documents(user_id),
            "contacts": list_contacts(user_id),
            "employees": list_employees(user_id),
            "obligations": list_obligations(user_id),
        }
    try:
        with engine.connect() as conn:
            raw = conn.execute(
                text("select public.razync_user_snapshot(:uid)"),
                {"uid": int(user_id)},
            ).scalar_one()
    except OperationalError as exc:
        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None

    if isinstance(raw, str):
        raw = json.loads(raw)
    snapshot = dict(raw or {})
    snapshot.setdefault("profile", {})
    for key in ("transactions", "invoices", "das", "documents", "contacts", "employees", "obligations"):
        snapshot.setdefault(key, [])

    profile = snapshot.get("profile") or {}
    if profile.get("opening_date"):
        profile["opening_date"] = _snapshot_date(profile.get("opening_date"))
    snapshot["profile"] = profile

    for row in snapshot["transactions"]:
        row["tx_date"] = _snapshot_date(row.get("tx_date"))
    for row in snapshot["invoices"]:
        row["issue_date"] = _snapshot_date(row.get("issue_date"))
    for row in snapshot["das"]:
        row["due_date"] = _snapshot_date(row.get("due_date"))
        row["payment_date"] = _snapshot_date(row.get("payment_date"))
    for row in snapshot["employees"]:
        row["admission_date"] = _snapshot_date(row.get("admission_date"))
    for row in snapshot["obligations"]:
        row["due_date"] = _snapshot_date(row.get("due_date"))
    return snapshot


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
    name = name.strip()
    email = email.strip().lower()

    if len(name) < 2:
        return False, "Informe seu nome."
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        return False, "Informe um e-mail válido."
    if len(password) < 8:
        return False, "A senha precisa ter pelo menos 8 caracteres."
    if len(password) > 128:
        return False, "A senha deve ter no máximo 128 caracteres."

    try:
        with engine.begin() as conn:
            result = conn.execute(
                insert(users).values(
                    name=name,
                    email=email,
                    password_hash=_hash_password(password),
                )
            )
            uid = int(result.inserted_primary_key[0])
            conn.execute(insert(profiles).values(user_id=uid))
        return True, "Conta criada com sucesso."
    except IntegrityError:
        return False, "Já existe uma conta com este e-mail."
    except OperationalError as exc:
        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    email = email.strip().lower()
    if not email or not password:
        return None

    try:
        with engine.connect() as conn:
            row = conn.execute(
                select(users).where(users.c.email == email)
            ).mappings().first()
    except OperationalError as exc:
        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None

    if not row or not _verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def resolve_supabase_user(auth_user_id: str, email: str, name: str = "") -> dict[str, Any]:
    """Resolve or safely link a confirmed Supabase identity to a legacy account."""
    normalized_email = email.strip().lower()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                select(users).where(users.c.auth_user_id == auth_user_id)
            ).mappings().first()
            if row is None:
                row = conn.execute(
                    select(users).where(users.c.email == normalized_email)
                ).mappings().first()
                if row is not None:
                    if row.get("auth_user_id") not in (None, auth_user_id):
                        raise ValueError("Esta conta já está vinculada a outra identidade.")
                    conn.execute(
                        update(users)
                        .where(users.c.id == row["id"])
                        .values(auth_user_id=auth_user_id)
                    )
                    row = dict(row)
                    row["auth_user_id"] = auth_user_id
                else:
                    result = conn.execute(
                        insert(users).values(
                            name=name.strip() or normalized_email.split("@", 1)[0],
                            email=normalized_email,
                            auth_user_id=auth_user_id,
                            password_hash=_hash_password(os.urandom(32).hex()),
                        )
                    )
                    uid = int(result.inserted_primary_key[0])
                    conn.execute(insert(profiles).values(user_id=uid))
                    row = conn.execute(
                        select(users).where(users.c.id == uid)
                    ).mappings().one()
    except (IntegrityError, OperationalError) as exc:
        if isinstance(exc, OperationalError):
            raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None
        raise ValueError("Não foi possível vincular esta identidade.") from None

    return {"id": row["id"], "name": row["name"], "email": row["email"], "auth_user_id": auth_user_id}


def get_profile(user_id: int) -> dict[str, Any]:
    cached = _cache_get("profile", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        row = conn.execute(select(users.c.name, users.c.email, profiles).join(profiles, profiles.c.user_id == users.c.id).where(users.c.id == user_id)).mappings().first()
    return _cache_set("profile", user_id, dict(row) if row else {})


def save_profile(user_id: int, **data: Any) -> None:
    allowed = {c.name for c in profiles.c if c.name != "user_id"}
    payload = {k: v for k, v in data.items() if k in allowed}
    with engine.begin() as conn:
        existing = conn.execute(select(profiles.c.user_id).where(profiles.c.user_id == user_id)).first()
        if existing:
            conn.execute(update(profiles).where(profiles.c.user_id == user_id).values(**payload))
        else:
            conn.execute(insert(profiles).values(user_id=user_id, **payload))
    _cache_invalidate("profile", user_id)


def add_recurring_transaction(user_id: int, **data: Any) -> None:
    allowed = {
        "tx_type", "description", "category", "value", "payment_method",
        "frequency", "next_date", "end_date", "active",
    }
    payload = {key: value for key, value in data.items() if key in allowed}
    with engine.begin() as conn:
        conn.execute(insert(recurring_transactions).values(user_id=user_id, **payload))
    _cache_invalidate("recurring_transactions", user_id)
    _RECURRING_MATERIALIZE_CHECK.pop(int(user_id), None)


def list_recurring_transactions(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("recurring_transactions", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(
            select(recurring_transactions)
            .where(recurring_transactions.c.user_id == user_id)
            .order_by(recurring_transactions.c.active.desc(), recurring_transactions.c.next_date.asc())
        ).mappings().all()
    return _cache_set("recurring_transactions", user_id, [dict(row) for row in rows])


def set_recurring_transaction_active(user_id: int, item_id: int, active: bool) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            update(recurring_transactions)
            .where(
                recurring_transactions.c.user_id == user_id,
                recurring_transactions.c.id == item_id,
            )
            .values(active=bool(active))
        )
    _cache_invalidate("recurring_transactions", user_id)
    _RECURRING_MATERIALIZE_CHECK.pop(int(user_id), None)
    return bool(result.rowcount)


def delete_recurring_transaction(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            delete(recurring_transactions).where(
                recurring_transactions.c.user_id == user_id,
                recurring_transactions.c.id == item_id,
            )
        )
    _cache_invalidate("recurring_transactions", user_id)
    _RECURRING_MATERIALIZE_CHECK.pop(int(user_id), None)


def materialize_due_recurring(
    user_id: int,
    today: date | None = None,
    max_occurrences: int = 36,
) -> int:
    """Create due transactions once and advance each schedule safely."""
    today = today or date.today()
    uid = int(user_id)
    if _RECURRING_MATERIALIZE_CHECK.get(uid) == today:
        return 0
    generated = 0
    with engine.begin() as conn:
        rows = conn.execute(
            select(recurring_transactions)
            .where(
                recurring_transactions.c.user_id == user_id,
                recurring_transactions.c.active.is_(True),
                recurring_transactions.c.next_date <= today,
            )
            .order_by(recurring_transactions.c.next_date.asc())
        ).mappings().all()

        for row in rows:
            occurrence = row["next_date"]
            end_date = row.get("end_date")
            while occurrence <= today and generated < max_occurrences:
                if end_date and occurrence > end_date:
                    break
                exists = conn.execute(
                    select(transactions.c.id).where(
                        transactions.c.recurring_transaction_id == row["id"],
                        transactions.c.tx_date == occurrence,
                    )
                ).first()
                if not exists:
                    conn.execute(
                        insert(transactions).values(
                            user_id=user_id,
                            tx_date=occurrence,
                            tx_type=row["tx_type"],
                            description=row["description"],
                            category=row["category"],
                            value=row["value"],
                            document_number="",
                            counterparty="",
                            payment_method=row["payment_method"],
                            recurring_transaction_id=row["id"],
                        )
                    )
                    generated += 1
                occurrence = next_recurrence_date(occurrence, row["frequency"])

            still_active = not end_date or occurrence <= end_date
            conn.execute(
                update(recurring_transactions)
                .where(
                    recurring_transactions.c.user_id == user_id,
                    recurring_transactions.c.id == row["id"],
                )
                .values(next_date=occurrence, active=still_active)
            )

    if rows:
        _cache_invalidate("recurring_transactions", user_id)
    if generated:
        _cache_invalidate("transactions", user_id)
        _cache_invalidate("tx_docs", user_id)
        for key in [key for key in list(_READ_CACHE) if key[0] == "dashboard"]:
            _READ_CACHE.pop(key, None)
    if generated < max_occurrences:
        _RECURRING_MATERIALIZE_CHECK[uid] = today
    else:
        _RECURRING_MATERIALIZE_CHECK.pop(uid, None)
    return generated


def add_transaction(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(transactions).values(user_id=user_id, **data))
    _cache_invalidate("transactions", user_id)
    for _k in [k for k in list(_READ_CACHE) if k[0] == "dashboard"]: _READ_CACHE.pop(_k, None)
    _cache_invalidate("tx_docs", user_id)


def update_transaction(user_id: int, item_id: int, **data: Any) -> bool:
    """Update an owned transaction and invalidate every derived cache."""
    allowed = {
        "tx_date", "tx_type", "description", "category", "value",
        "document_number", "counterparty", "payment_method",
    }
    payload = {key: value for key, value in data.items() if key in allowed}
    if not payload:
        return False
    with engine.begin() as conn:
        result = conn.execute(
            update(transactions)
            .where(transactions.c.user_id == user_id, transactions.c.id == item_id)
            .values(**payload)
        )
    _cache_invalidate("transactions", user_id)
    for key in [key for key in list(_READ_CACHE) if key[0] == "dashboard"]:
        _READ_CACHE.pop(key, None)
    _cache_invalidate("tx_docs", user_id)
    return bool(result.rowcount)


def list_transactions(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("transactions", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc())).mappings().all()
    return _cache_set("transactions", user_id, [dict(r) for r in rows])


def dashboard_financial_summary(user_id: int, year: int, month: int) -> dict[str, Any]:
    cache_key = int(user_id) * 100000 + int(year) * 100 + int(month)
    cached = _cache_get("dashboard", cache_key)
    if cached is not None:
        return cached
    year_cond = extract("year", transactions.c.tx_date) == int(year)
    month_cond = extract("month", transactions.c.tx_date) == int(month)
    stmt = select(
        func.count(transactions.c.id).label("transaction_count"),
        func.coalesce(func.sum(case((year_cond & (transactions.c.tx_type == "Receita"), transactions.c.value), else_=0)), 0).label("year_revenue"),
        func.coalesce(func.sum(case((year_cond & (transactions.c.tx_type == "Despesa"), transactions.c.value), else_=0)), 0).label("year_expense"),
        func.coalesce(func.sum(case((year_cond & month_cond & (transactions.c.tx_type == "Receita"), transactions.c.value), else_=0)), 0).label("month_in"),
        func.coalesce(func.sum(case((year_cond & month_cond & (transactions.c.tx_type == "Despesa"), transactions.c.value), else_=0)), 0).label("month_out"),
    ).where(transactions.c.user_id == user_id)
    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().one()
    result = {k: float(v or 0) if k != "transaction_count" else int(v or 0) for k, v in dict(row).items()}
    return _cache_set("dashboard", cache_key, result)

def transaction_document_numbers(user_id: int) -> list[str]:
    cached = _cache_get("tx_docs", user_id)
    if cached is not None:
        return cached
    stmt = select(transactions.c.document_number).where(
        transactions.c.user_id == user_id,
        transactions.c.document_number.is_not(None),
        transactions.c.document_number != ""
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).scalars().all()
    return _cache_set("tx_docs", user_id, [str(x) for x in rows])

def count_transactions(user_id: int) -> int:
    with engine.connect() as conn:
        return int(conn.execute(select(func.count()).select_from(transactions).where(transactions.c.user_id == user_id)).scalar_one())

def list_transactions_page(user_id: int, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    stmt = select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc()).limit(int(limit)).offset(int(offset))
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [dict(r) for r in rows]


def delete_transaction(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(transactions).where(transactions.c.user_id == user_id, transactions.c.id == item_id))
    _cache_invalidate("transactions", user_id)
    for _k in [k for k in list(_READ_CACHE) if k[0] == "dashboard"]: _READ_CACHE.pop(_k, None)
    _cache_invalidate("tx_docs", user_id)


def link_transaction_document(user_id: int, item_id: int, document_number: str, counterparty: str = "") -> None:
    payload = {"document_number": (document_number or "").strip()}
    if counterparty:
        payload["counterparty"] = counterparty.strip()
    with engine.begin() as conn:
        conn.execute(update(transactions).where(transactions.c.user_id == user_id, transactions.c.id == item_id).values(**payload))
    _cache_invalidate("transactions", user_id)
    for _k in [k for k in list(_READ_CACHE) if k[0] == "dashboard"]: _READ_CACHE.pop(_k, None)
    _cache_invalidate("tx_docs", user_id)


def upsert_das(user_id: int, competence: str, due_date, amount: float, status: str, payment_date, notes: str) -> None:
    with engine.begin() as conn:
        row = conn.execute(select(das_items.c.id).where(das_items.c.user_id == user_id, das_items.c.competence == competence)).first()
        payload = dict(due_date=due_date, amount=amount, status=status, payment_date=payment_date, notes=notes)
        if row:
            conn.execute(update(das_items).where(das_items.c.id == row[0]).values(**payload))
        else:
            conn.execute(insert(das_items).values(user_id=user_id, competence=competence, **payload))
    _cache_invalidate("das", user_id)


def list_das(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("das", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(das_items).where(das_items.c.user_id == user_id).order_by(das_items.c.competence.desc())).mappings().all()
    return _cache_set("das", user_id, [dict(r) for r in rows])


def save_document(
    user_id: int,
    filename: str,
    mime_type: str,
    content: bytes | None,
    category: str,
    reference_month: str = "",
    storage_path: str | None = None,
) -> None:
    if content is None and not storage_path:
        raise ValueError("Documento sem conteúdo ou caminho de armazenamento.")
    with engine.begin() as conn:
        conn.execute(
            insert(documents).values(
                user_id=user_id,
                filename=filename,
                mime_type=mime_type,
                content=content,
                storage_path=storage_path,
                category=category,
                reference_month=reference_month,
            )
        )
    _cache_invalidate("documents", user_id)


def list_documents(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("documents", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(documents.c.id, documents.c.filename, documents.c.mime_type, documents.c.category, documents.c.reference_month, documents.c.created_at).where(documents.c.user_id == user_id).order_by(documents.c.id.desc())).mappings().all()
    return _cache_set("documents", user_id, [dict(r) for r in rows])


def get_document(user_id: int, item_id: int) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(select(documents).where(documents.c.user_id == user_id, documents.c.id == item_id)).mappings().first()
    return dict(row) if row else None


def delete_document(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(documents).where(documents.c.user_id == user_id, documents.c.id == item_id))
    _cache_invalidate("documents", user_id)


def add_invoice(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(invoices).values(user_id=user_id, **data))
    _cache_invalidate("invoices", user_id)


def list_invoices(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("invoices", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(invoices).where(invoices.c.user_id == user_id).order_by(invoices.c.issue_date.desc(), invoices.c.id.desc())).mappings().all()
    return _cache_set("invoices", user_id, [dict(r) for r in rows])


def delete_invoice(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(invoices).where(invoices.c.user_id == user_id, invoices.c.id == item_id))
    _cache_invalidate("invoices", user_id)


def add_contact(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(contacts).values(user_id=user_id, **data))
    _cache_invalidate("contacts", user_id)


def list_contacts(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("contacts", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(contacts).where(contacts.c.user_id == user_id).order_by(contacts.c.name.asc())).mappings().all()
    return _cache_set("contacts", user_id, [dict(r) for r in rows])


def delete_contact(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(contacts).where(contacts.c.user_id == user_id, contacts.c.id == item_id))
    _cache_invalidate("contacts", user_id)


def add_employee(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(employees).values(user_id=user_id, **data))
    _cache_invalidate("employees", user_id)


def list_employees(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("employees", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(employees).where(employees.c.user_id == user_id).order_by(employees.c.name.asc())).mappings().all()
    return _cache_set("employees", user_id, [dict(r) for r in rows])


def delete_employee(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(employees).where(employees.c.user_id == user_id, employees.c.id == item_id))
    _cache_invalidate("employees", user_id)


def add_obligation(user_id: int, **data: Any) -> None:
    with engine.begin() as conn:
        conn.execute(insert(obligations).values(user_id=user_id, **data))
    _cache_invalidate("obligations", user_id)


def list_obligations(user_id: int) -> list[dict[str, Any]]:
    cached = _cache_get("obligations", user_id)
    if cached is not None:
        return cached
    with engine.connect() as conn:
        rows = conn.execute(select(obligations).where(obligations.c.user_id == user_id).order_by(obligations.c.due_date.asc())).mappings().all()
    return _cache_set("obligations", user_id, [dict(r) for r in rows])


def update_obligation_status(user_id: int, item_id: int, status: str) -> None:
    with engine.begin() as conn:
        conn.execute(update(obligations).where(obligations.c.user_id == user_id, obligations.c.id == item_id).values(status=status))
    _cache_invalidate("obligations", user_id)


def delete_obligation(user_id: int, item_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(delete(obligations).where(obligations.c.user_id == user_id, obligations.c.id == item_id))
    _cache_invalidate("obligations", user_id)
