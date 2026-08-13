from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

DB_PATH = Path("razync_pro.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mei_profiles (
                user_id INTEGER PRIMARY KEY,
                business_name TEXT DEFAULT '',
                cnpj TEXT DEFAULT '',
                main_activity TEXT DEFAULT '',
                opening_date TEXT,
                annual_limit REAL NOT NULL DEFAULT 0,
                phone TEXT DEFAULT '',
                city TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tx_date TEXT NOT NULL,
                tx_type TEXT NOT NULL CHECK(tx_type IN ('Receita', 'Despesa')),
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                value REAL NOT NULL CHECK(value >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS das_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                competence TEXT NOT NULL,
                due_date TEXT,
                amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Pendente',
                payment_date TEXT,
                notes TEXT DEFAULT '',
                UNIQUE(user_id, competence),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                content BLOB NOT NULL,
                category TEXT DEFAULT 'Outros',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return f"{salt.hex()}:{digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return hmac.compare_digest(actual, expected)


def create_user(name: str, email: str, password: str) -> tuple[bool, str]:
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), _hash_password(password)),
            )
            user_id = int(cur.lastrowid)
            conn.execute(
                "INSERT OR IGNORE INTO mei_profiles (user_id, opening_date, annual_limit) VALUES (?, ?, ?)",
                (user_id, date.today().isoformat(), 0),
            )
        return True, "Conta criada com sucesso."
    except sqlite3.IntegrityError:
        return False, "Já existe uma conta com este e-mail."


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    if not row or not _verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def get_profile(user_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT u.name, u.email, p.business_name, p.cnpj, p.main_activity,
                   p.opening_date, p.annual_limit, p.phone, p.city
            FROM users u
            LEFT JOIN mei_profiles p ON p.user_id = u.id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else {}


def save_profile(user_id: int, business_name: str, cnpj: str, main_activity: str, opening_date: str, annual_limit: float, phone: str, city: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO mei_profiles
                (user_id, business_name, cnpj, main_activity, opening_date, annual_limit, phone, city)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                business_name = excluded.business_name,
                cnpj = excluded.cnpj,
                main_activity = excluded.main_activity,
                opening_date = excluded.opening_date,
                annual_limit = excluded.annual_limit,
                phone = excluded.phone,
                city = excluded.city
            """,
            (user_id, business_name, cnpj, main_activity, opening_date, annual_limit, phone, city),
        )


def add_transaction(user_id: int, tx_date: str, tx_type: str, description: str, category: str, value: float) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO transactions (user_id, tx_date, tx_type, description, category, value) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, tx_date, tx_type, description, category, value),
        )


def list_transactions(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, tx_date, tx_type, description, category, value, created_at FROM transactions WHERE user_id = ? ORDER BY tx_date DESC, id DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_transaction(user_id: int, transaction_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM transactions WHERE user_id = ? AND id = ?", (user_id, transaction_id))


def upsert_das(user_id: int, competence: str, due_date: str | None, amount: float, status: str, payment_date: str | None, notes: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO das_items (user_id, competence, due_date, amount, status, payment_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, competence) DO UPDATE SET
                due_date = excluded.due_date,
                amount = excluded.amount,
                status = excluded.status,
                payment_date = excluded.payment_date,
                notes = excluded.notes
            """,
            (user_id, competence, due_date, amount, status, payment_date, notes),
        )


def list_das(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, competence, due_date, amount, status, payment_date, notes FROM das_items WHERE user_id = ? ORDER BY competence DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def save_document(user_id: int, filename: str, mime_type: str, content: bytes, category: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO documents (user_id, filename, mime_type, content, category) VALUES (?, ?, ?, ?, ?)",
            (user_id, filename, mime_type, content, category),
        )


def list_documents(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, filename, mime_type, category, created_at, length(content) AS size_bytes FROM documents WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_document(user_id: int, document_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, filename, mime_type, content, category FROM documents WHERE user_id = ? AND id = ?",
            (user_id, document_id),
        ).fetchone()
    return dict(row) if row else None


def delete_document(user_id: int, document_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE user_id = ? AND id = ?", (user_id, document_id))
