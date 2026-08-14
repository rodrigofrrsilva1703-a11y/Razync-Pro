from __future__ import annotations

from io import BytesIO
from datetime import datetime, timezone
from hashlib import sha256
import json
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


def build_backup_zip(
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    contacts: list[dict],
    employees: list[dict],
    documents: list[dict],
    document_loader=None,
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
        included_documents = 0
        if document_loader:
            for document in documents:
                try:
                    loaded = document_loader(int(document["id"]))
                    content = (loaded or {}).get("content")
                    if content:
                        safe_name = str(document.get("filename") or f"documento-{document['id']}").replace("/", "_").replace("\\", "_")
                        zf.writestr(f"documentos/{document['id']}-{safe_name}", content)
                        included_documents += 1
                except Exception:
                    continue
        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "format_version": 2,
            "transactions": len(transactions),
            "invoices": len(invoices),
            "documents_indexed": len(documents),
            "documents_included": included_documents,
        }
        zf.writestr("manifesto.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("LEIA-ME.txt", "Backup exportado pelo Razync Pro. Guarde este arquivo em local seguro. Os CSVs representam os dados no momento da exportação.")
    return buffer.getvalue()


def backup_checksum(payload: bytes) -> str:
    """Return a short integrity fingerprint users can keep with the backup."""
    return sha256(payload).hexdigest()


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

# trigger finish product workflow
