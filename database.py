from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).with_name("mei_facil.db")


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK (tipo IN ('Receita', 'Despesa')),
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL CHECK (valor >= 0),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mei (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nome TEXT DEFAULT '',
                cnpj TEXT DEFAULT '',
                atividade TEXT DEFAULT '',
                data_abertura TEXT,
                limite_anual REAL DEFAULT 0
            );
            """
        )


def add_lancamento(data: str, tipo: str, descricao: str, categoria: str, valor: float) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO lancamentos (data, tipo, descricao, categoria, valor)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data, tipo, descricao.strip(), categoria, float(valor)),
        )


def delete_lancamento(lancamento_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM lancamentos WHERE id = ?", (int(lancamento_id),))


def get_lancamentos(tipo: str | None = None) -> pd.DataFrame:
    query = "SELECT id, data, tipo, descricao, categoria, valor FROM lancamentos"
    params: tuple = ()
    if tipo:
        query += " WHERE tipo = ?"
        params = (tipo,)
    query += " ORDER BY date(data) DESC, id DESC"

    with connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])
    return df


def get_resumo() -> dict[str, float]:
    with connection() as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN tipo = 'Receita' THEN valor ELSE 0 END), 0) AS receitas,
                COALESCE(SUM(CASE WHEN tipo = 'Despesa' THEN valor ELSE 0 END), 0) AS despesas,
                COUNT(*) AS quantidade
            FROM lancamentos
            """
        ).fetchone()

    receitas = float(row["receitas"])
    despesas = float(row["despesas"])
    return {
        "receitas": receitas,
        "despesas": despesas,
        "resultado": receitas - despesas,
        "quantidade": int(row["quantidade"]),
    }


def get_fluxo_mensal() -> pd.DataFrame:
    with connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                substr(data, 1, 7) AS mes,
                SUM(CASE WHEN tipo = 'Receita' THEN valor ELSE 0 END) AS receitas,
                SUM(CASE WHEN tipo = 'Despesa' THEN valor ELSE 0 END) AS despesas
            FROM lancamentos
            GROUP BY substr(data, 1, 7)
            ORDER BY mes
            """,
            conn,
        )
    if not df.empty:
        df["saldo"] = df["receitas"] - df["despesas"]
    return df


def save_mei(nome: str, cnpj: str, atividade: str, data_abertura: str, limite_anual: float) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO mei (id, nome, cnpj, atividade, data_abertura, limite_anual)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome = excluded.nome,
                cnpj = excluded.cnpj,
                atividade = excluded.atividade,
                data_abertura = excluded.data_abertura,
                limite_anual = excluded.limite_anual
            """,
            (nome.strip(), cnpj.strip(), atividade.strip(), data_abertura, float(limite_anual)),
        )


def get_mei() -> dict[str, object]:
    with connection() as conn:
        row = conn.execute(
            "SELECT nome, cnpj, atividade, data_abertura, limite_anual FROM mei WHERE id = 1"
        ).fetchone()

    if row is None:
        return {"nome": "", "cnpj": "", "atividade": "", "data_abertura": None, "limite_anual": 0.0}
    return dict(row)
