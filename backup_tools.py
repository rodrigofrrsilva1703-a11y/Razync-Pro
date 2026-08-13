from __future__ import annotations

from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


def build_backup_zip(
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    contacts: list[dict],
    obligations: list[dict],
    employees: list[dict],
    documents: list[dict],
) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        zf.writestr("perfil_mei.json", json.dumps(profile, ensure_ascii=False, indent=2, default=str))
        zf.writestr("movimentacoes.csv", transactions.to_csv(index=False))
        zf.writestr("notas_fiscais.csv", invoices.to_csv(index=False))
        zf.writestr("das.csv", pd.DataFrame(das_rows).to_csv(index=False))
        zf.writestr("contatos.csv", pd.DataFrame(contacts).to_csv(index=False))
        zf.writestr("obrigacoes.csv", pd.DataFrame(obligations).to_csv(index=False))
        zf.writestr("empregados.csv", pd.DataFrame(employees).to_csv(index=False))
        zf.writestr("indice_documentos.csv", pd.DataFrame(documents).to_csv(index=False))
        zf.writestr("LEIA-ME.txt", "Backup exportado pelo Razync Pro. Os arquivos CSV usam os dados cadastrados no sistema no momento da exportação.")
    return buffer.getvalue()


def document_coverage(documents: list[dict], year: int) -> pd.DataFrame:
    rows = []
    for month in range(1, 13):
        ref = f"{year}-{month:02d}"
        month_docs = [d for d in documents if str(d.get("reference_month") or "").strip() == ref]
        categories = sorted({str(d.get("category") or "Outro") for d in month_docs})
        rows.append({
            "Competência": ref,
            "Documentos": len(month_docs),
            "Categorias": ", ".join(categories) if categories else "-",
            "Status": "Com documentos" if month_docs else "Sem documentos",
        })
    return pd.DataFrame(rows)
