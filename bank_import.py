from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
import re

import pandas as pd


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def read_statement(uploaded_file) -> pd.DataFrame:
    """Lê CSV ou XLSX e devolve um DataFrame sem assumir layout bancário."""
    name = (uploaded_file.name or "").lower()
    raw = uploaded_file.getvalue()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        return _normalize_columns(pd.read_excel(BytesIO(raw)))

    if name.endswith(".csv") or name.endswith(".txt"):
        text = raw.decode("utf-8-sig", errors="replace")
        # Tenta detectar automaticamente ; , e tab.
        for sep in [None, ";", ",", "\t"]:
            try:
                df = pd.read_csv(StringIO(text), sep=sep, engine="python")
                if len(df.columns) > 1:
                    return _normalize_columns(df)
            except Exception:
                pass
        raise ValueError("Não foi possível identificar as colunas do arquivo CSV.")

    raise ValueError("Formato não suportado. Use CSV ou XLSX.")


def parse_money(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text:
        return 0.0
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def prepare_statement(
    df: pd.DataFrame,
    date_col: str,
    description_col: str,
    value_col: str,
    direction: str = "Sinal do valor",
) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Data"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    out["Descrição"] = df[description_col].fillna("").astype(str).str.strip()
    out["Valor original"] = df[value_col].map(parse_money)
    out = out.dropna(subset=["Data"])
    out = out[out["Valor original"] != 0].copy()

    if direction == "Tudo como receita":
        out["Tipo"] = "Receita"
        out["Valor"] = out["Valor original"].abs()
    elif direction == "Tudo como despesa":
        out["Tipo"] = "Despesa"
        out["Valor"] = out["Valor original"].abs()
    else:
        out["Tipo"] = out["Valor original"].apply(lambda x: "Receita" if x > 0 else "Despesa")
        out["Valor"] = out["Valor original"].abs()

    out["Data"] = out["Data"].dt.date
    return out[["Data", "Tipo", "Descrição", "Valor"]].reset_index(drop=True)


def is_probable_duplicate(existing: pd.DataFrame, tx_date, tx_type: str, description: str, value: float) -> bool:
    if existing.empty:
        return False
    df = existing.copy()
    if "tx_date" not in df.columns:
        return False
    dates = pd.to_datetime(df["tx_date"], errors="coerce").dt.date
    same_date = dates == tx_date
    same_type = df["tx_type"].astype(str) == tx_type
    same_value = (pd.to_numeric(df["value"], errors="coerce").fillna(0) - float(value)).abs() < 0.01
    normalized = re.sub(r"\s+", " ", description.strip().lower())
    existing_desc = df["description"].fillna("").astype(str).str.lower().str.replace(r"\s+", " ", regex=True)
    same_desc = existing_desc == normalized
    return bool((same_date & same_type & same_value & same_desc).any())


def suggest_category(description: str, tx_type: str) -> str:
    text = description.lower()
    if tx_type == "Receita":
        return "Serviços" if any(k in text for k in ["serv", "honor", "cliente", "nfse"]) else "Vendas"
    rules = [
        (["imposto", "das", "tribut"], "Impostos"),
        (["alug", "loca"], "Aluguel"),
        (["uber", "99", "combust", "posto", "transport"], "Transporte"),
        (["meta", "google", "ads", "marketing"], "Marketing"),
        (["salario", "folha", "funcion"], "Folha"),
    ]
    for keys, category in rules:
        if any(k in text for k in keys):
            return category
    return "Fornecedores"
