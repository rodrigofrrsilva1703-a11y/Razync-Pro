from __future__ import annotations

from difflib import SequenceMatcher
import pandas as pd


def _text(v) -> str:
    return str(v or "").strip().lower()


def _similarity(a, b) -> float:
    a, b = _text(a), _text(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def candidate_score(invoice: pd.Series, tx: pd.Series) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    inv_number = _text(invoice.get("number"))
    tx_doc = _text(tx.get("document_number"))
    if inv_number and tx_doc and inv_number == tx_doc:
        score += 60; reasons.append("mesmo número de documento")

    inv_value = float(invoice.get("amount") or 0)
    tx_value = float(tx.get("value") or 0)
    if inv_value and abs(inv_value - tx_value) < 0.01:
        score += 25; reasons.append("mesmo valor")
    elif inv_value and abs(inv_value - tx_value) <= max(2.0, inv_value * .01):
        score += 15; reasons.append("valor muito próximo")

    inv_date = pd.to_datetime(invoice.get("issue_date"), errors="coerce")
    tx_date = pd.to_datetime(tx.get("tx_date"), errors="coerce")
    if pd.notna(inv_date) and pd.notna(tx_date):
        days = abs((inv_date.normalize() - tx_date.normalize()).days)
        if days == 0:
            score += 10; reasons.append("mesma data")
        elif days <= 3:
            score += 7; reasons.append("data próxima")
        elif days <= 10:
            score += 3

    customer = _text(invoice.get("customer"))
    tx_party = " ".join([_text(tx.get("counterparty")), _text(tx.get("description"))]).strip()
    sim = _similarity(customer, tx_party)
    if sim >= .85:
        score += 10; reasons.append("cliente compatível")
    elif sim >= .60:
        score += 5; reasons.append("cliente parecido")

    return min(score, 100), reasons


def smart_invoice_matches(transactions: pd.DataFrame, invoices: pd.DataFrame) -> pd.DataFrame:
    columns = ["invoice_id","invoice_number","customer","invoice_value","tx_id","tx_date","tx_description","tx_value","score","confidence","reasons"]
    if transactions.empty or invoices.empty:
        return pd.DataFrame(columns=columns)
    revenue = transactions[transactions["tx_type"] == "Receita"].copy()
    emitted = invoices[invoices["status"] == "Emitida"].copy() if "status" in invoices else invoices.copy()
    rows = []
    for _, inv in emitted.iterrows():
        best = None
        for _, tx in revenue.iterrows():
            score, reasons = candidate_score(inv, tx)
            if best is None or score > best[0]:
                best = (score, reasons, tx)
        if best and best[0] >= 25:
            score, reasons, tx = best
            confidence = "Alta" if score >= 70 else "Média" if score >= 45 else "Baixa"
            rows.append({
                "invoice_id": int(inv.get("id")), "invoice_number": str(inv.get("number") or ""),
                "customer": str(inv.get("customer") or ""), "invoice_value": float(inv.get("amount") or 0),
                "tx_id": int(tx.get("id")), "tx_date": tx.get("tx_date"), "tx_description": str(tx.get("description") or ""),
                "tx_value": float(tx.get("value") or 0), "score": score, "confidence": confidence,
                "reasons": ", ".join(reasons) if reasons else "sem sinal forte",
            })
    return pd.DataFrame(rows, columns=columns).sort_values(["score","invoice_id"], ascending=[False, True]) if rows else pd.DataFrame(columns=columns)


def duplicate_groups(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame(columns=["id","tx_date","tx_type","description","value"])
    temp = transactions.copy()
    temp["_desc"] = temp["description"].fillna("").astype(str).str.lower().str.strip()
    dup = temp[temp.duplicated(subset=["tx_date","tx_type","value","_desc"], keep=False)].copy()
    return dup[["id","tx_date","tx_type","description","value"]].sort_values(["tx_date","value","description"]) if not dup.empty else dup[["id","tx_date","tx_type","description","value"]]
