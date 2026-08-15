from __future__ import annotations

from datetime import UTC, date, datetime
from io import BytesIO, StringIO
import re
import unicodedata
from typing import Iterable

import pandas as pd

from fiscal_rules import das_status
from customer_experience import integration_catalog


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
    return None


def build_notifications(das_rows: Iterable[dict], obligations: Iterable[dict], annual_revenue: float, annual_limit: float, today: date | None = None) -> list[dict]:
    """Builds a deterministic, user-scoped notification feed."""
    today = today or date.today()
    items: list[dict] = []
    for row in das_rows:
        due = _as_date(row.get("due_date"))
        status = das_status(row.get("status", "Pendente"), due, today)
        if status == "Atrasado":
            items.append({"level": "urgent", "title": f"DAS {row.get('competence', '')} em atraso", "detail": f"Vencimento em {due.strftime('%d/%m/%Y') if due else 'data não informada'}. Atualize após o pagamento.", "page": "DAS", "due_date": due})
        elif status == "Pendente" and due and 0 <= (due - today).days <= 10:
            items.append({"level": "warning", "title": f"DAS {row.get('competence', '')} vence em breve", "detail": f"Vencimento em {due.strftime('%d/%m/%Y')}.", "page": "DAS", "due_date": due})
    for row in obligations:
        due = _as_date(row.get("due_date"))
        if row.get("status") == "Concluído" or not due:
            continue
        days = (due - today).days
        if days < 0:
            level, detail = "urgent", f"Venceu em {due.strftime('%d/%m/%Y')}"
        elif days <= 15:
            level, detail = "warning", f"Vence em {due.strftime('%d/%m/%Y')}"
        else:
            continue
        items.append({"level": level, "title": row.get("title") or "Obrigação", "detail": detail, "page": "Obrigações", "due_date": due})
    if annual_limit > 0:
        used = annual_revenue / annual_limit
        if used >= 0.8:
            items.append({"level": "urgent" if used >= 0.95 else "warning", "title": "Limite anual do MEI", "detail": f"{used * 100:.1f}% do limite monitorado já foi utilizado.", "page": "Análise Financeira", "due_date": None})
    rank = {"urgent": 0, "warning": 1, "info": 2}
    return sorted(items, key=lambda item: (rank.get(item["level"], 9), item.get("due_date") or date.max))


def notification_calendar(items: Iterable[dict], product_url: str) -> bytes:
    """Exports actionable due dates as a UTF-8 iCalendar file."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Razync Pro//Agenda MEI//PT-BR", "CALSCALE:GREGORIAN"]
    for index, item in enumerate(items):
        due = _as_date(item.get("due_date"))
        if not due:
            continue
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        uid = f"razync-{due.isoformat()}-{index}@razync.pro"
        title = re.sub(r"[\r\n,;]+", " ", str(item.get("title") or "Prazo do MEI"))
        detail = re.sub(r"[\r\n]+", " ", str(item.get("detail") or ""))
        lines.extend(["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{due.strftime('%Y%m%d')}", f"SUMMARY:{title}", f"DESCRIPTION:{detail}", f"URL:{product_url}", "END:VEVENT"])
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def read_nfse_export(uploaded_file) -> pd.DataFrame:
    """Reads common NFS-e CSV/XLSX exports without storing the source file."""
    name = str(getattr(uploaded_file, "name", "")).lower()
    raw = uploaded_file.getvalue()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(raw))
    text = raw.decode("utf-8-sig", errors="replace")
    for sep in (None, ";", ",", "\t"):
        try:
            frame = pd.read_csv(StringIO(text), sep=sep, engine="python")
            if len(frame.columns) > 1:
                return frame
        except Exception:
            continue
    raise ValueError("Não foi possível ler o arquivo. Exporte as NFS-e em CSV ou XLSX.")


def suggest_nfse_columns(columns: Iterable[str]) -> dict[str, str | None]:
    def key(value: str) -> str:
        plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^a-z0-9]", "", plain.lower())
    normalized = {key(str(col)): str(col) for col in columns}
    aliases = {
        "date": ("dataemissao", "emissao", "datadanota", "data"),
        "number": ("numerodanota", "numeronfse", "numero", "nfse"),
        "customer": ("razaosocialtomador", "tomador", "cliente", "razaosocial"),
        "document": ("cpfcnpjtomador", "cnpjtomador", "cpftomador", "cpfcnpj"),
        "description": ("discriminacao", "descricao", "servico", "atividade"),
        "amount": ("valorliquido", "valordoservico", "valorservico", "valor"),
        "status": ("situacao", "status"),
    }
    result: dict[str, str | None] = {}
    for field, candidates in aliases.items():
        result[field] = next((normalized[key] for key in candidates if key in normalized), None)
    return result


def normalize_nfse(frame: pd.DataFrame, mapping: dict[str, str | None]) -> list[dict]:
    required = ("date", "number", "amount")
    if any(not mapping.get(field) for field in required):
        raise ValueError("Selecione as colunas de data, número e valor.")
    def text(row, field: str) -> str:
        column = mapping.get(field)
        if not column:
            return ""
        value = row.get(column, "")
        return "" if pd.isna(value) else str(value).strip()
    def money(value) -> float:
        if isinstance(value, (int, float)) and not pd.isna(value):
            return float(value)
        raw = re.sub(r"[^0-9,.-]", "", str(value or ""))
        if "," in raw:
            raw = raw.replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            return 0.0
    records = []
    for _, row in frame.iterrows():
        issued = pd.to_datetime(row.get(mapping["date"]), errors="coerce", dayfirst=True)
        number = text(row, "number")
        amount = money(row.get(mapping["amount"]))
        if pd.isna(issued) or not number or amount <= 0:
            continue
        raw_status = text(row, "status").lower()
        records.append({
            "issue_date": issued.date(), "invoice_type": "Serviço", "number": number,
            "customer": text(row, "customer"), "customer_document": text(row, "document"),
            "description": text(row, "description") or "Serviço", "amount": amount,
            "status": "Cancelada" if "cancel" in raw_status else "Emitida",
        })
    return records


def checkout_url(config: dict, plan: str) -> str:
    key = f"CHECKOUT_{plan.upper()}_URL"
    value = str(config.get(key, "")).strip()
    return value if value.startswith("https://") else ""


def integration_readiness(config: dict, database_persistent: bool) -> list[dict]:
    """Keep the legacy status API while using the richer integration catalog."""
    return [
        {
            "name": item["name"],
            "ready": item["ready"],
            "detail": f"{item['status']} · {item['detail']}",
        }
        for item in integration_catalog(config, database_persistent)
    ]
