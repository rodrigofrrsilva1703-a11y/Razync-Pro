from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

TRANSACTION_CATEGORIES = (
    "Serviços", "Vendas", "Materiais", "Aluguel", "Transporte",
    "Taxas", "Marketing", "Pró-labore/Retirada", "Outros",
)
PAYMENT_METHODS = ("PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro")
INVOICE_TYPES = ("Serviço", "Venda/Comércio")
RECURRENCE_FREQUENCIES = ("Semanal", "Mensal", "Anual")
_ACTION_VERBS = (
    "adicione", "adiciona", "adicionar", "anote", "anota", "anotar",
    "cadastre", "cadastra", "cadastrar", "coloque", "coloca", "colocar",
    "crie", "cria", "criar", "faça", "faca", "faz", "inclua", "inclui",
    "incluir", "insira", "insere", "inserir", "lance", "lança", "lanca",
    "lançar", "lancar", "registre", "registra", "registrar", "salve",
    "salva", "salvar", "gastei", "paguei", "comprei", "recebi", "vendi",
    "entrou", "saiu", "lembre", "lembra", "lembrete",
)
_GUIDANCE_PREFIXES = ("como ", "onde ", "posso ", "quero saber", "me explique", "qual ")
_BUSINESS_TIMEZONE = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class ActionDraft:
    action_type: str
    payload: dict[str, Any]
    missing_fields: tuple[str, ...]
    summary: str
    source: str = "local"
    action_key: str = field(default_factory=lambda: uuid4().hex)
    channel: str = "web"

    @property
    def ready(self) -> bool:
        return not self.missing_fields

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["missing_fields"] = list(self.missing_fields)
        data["ready"] = self.ready
        return data


class AssistantActionError(RuntimeError):
    """Safe error raised when an operational action cannot be prepared or saved."""


def _business_today() -> date:
    """Return the business date independently from the Streamlit server timezone."""
    return datetime.now(_BUSINESS_TIMEZONE).date()


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _looks_operational(question: str) -> bool:
    text = _plain(question).strip()
    if not text or text.startswith(_GUIDANCE_PREFIXES):
        return False
    return any(re.search(rf"\b{re.escape(verb)}\b", text) for verb in _ACTION_VERBS)


def _intent(question: str) -> str | None:
    if not _looks_operational(question):
        return None
    text = _plain(question)
    if any(term in text for term in ("me lembre", "lembrete", "obrigacao", "vencimento")):
        return "obligation"
    if re.search(r"\b(?:cadastre|cadastra|registre|registra|adicione|adiciona)\s+(?:o\s+|a\s+|um\s+|uma\s+)?(?:cliente|fornecedor|contato)\b", text):
        return "contact"
    if re.search(r"\b(nota fiscal|nfse|nfs-e|nf-e|nota\s+(?:n[ºo.]?\s*)?\w+)", text):
        return "invoice"
    if any(term in text for term in (
        "receita", "despesa", "gastei", "paguei", "comprei", "recebi",
        "vendi", "entrada", "saida", "lançamento", "lancamento",
        "movimentação", "movimentacao", "entrou", "saiu",
    )):
        if any(term in text for term in ("todo mes", "mensal", "mensalmente", "toda semana", "semanal", "semanalmente", "todo ano", "anual", "anualmente", "recorrente")):
            return "recurring_transaction"
        return "transaction"
    return None


def _parse_amount(text: str) -> float:
    without_dates = re.sub(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", " ", text)
    number = r"(\d+(?:\.\d{3})*(?:,\d{1,2})|\d+(?:[.,]\d{1,2})?)"
    currency = re.search(rf"r\$\s*{number}", without_dates, flags=re.I)
    explicit_value = re.search(rf"\b(?:no\s+valor\s+de|valor\s+de)\s*{number}", without_dates, flags=re.I)
    candidates = re.findall(number, without_dates, flags=re.I)
    raw = currency.group(1) if currency else explicit_value.group(1) if explicit_value else candidates[0] if candidates else ""
    if not raw:
        return 0.0
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return round(float(raw), 2)
    except ValueError:
        return 0.0


def _parse_date(value: str, today: date) -> date:
    text = _plain(value)
    if "ontem" in text:
        return today - timedelta(days=1)
    match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        raw_year = match.group(3)
        year = today.year if not raw_year else int(raw_year)
        if raw_year and len(raw_year) == 2:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            return today
    iso = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
    if iso:
        try:
            return date.fromisoformat(iso.group(0))
        except ValueError:
            pass
    return today


def _transaction_type(text: str) -> str:
    plain = _plain(text)
    if any(term in plain for term in ("despesa", "gastei", "paguei", "comprei", "saida", "saiu")):
        return "Despesa"
    if any(term in plain for term in ("receita", "recebi", "vendi", "entrada", "entrou")):
        return "Receita"
    return ""


def _category(text: str, tx_type: str) -> str:
    plain = _plain(text)
    rules = (
        (("servico", "serviço"), "Serviços"),
        (("venda", "produto"), "Vendas"),
        (("material", "insumo", "mercadoria"), "Materiais"),
        (("aluguel",), "Aluguel"),
        (("transporte", "combustivel", "uber", "frete"), "Transporte"),
        (("taxa", "tarifa", "imposto"), "Taxas"),
        (("marketing", "anuncio", "publicidade"), "Marketing"),
        (("pro-labore", "retirada"), "Pró-labore/Retirada"),
    )
    for terms, category in rules:
        if any(term in plain for term in terms):
            return category
    return "Serviços" if tx_type == "Receita" and "serv" in plain else "Outros"


def _payment_method(text: str) -> str:
    plain = _plain(text)
    rules = (
        (("pix",), "PIX"),
        (("dinheiro", "especie"), "Dinheiro"),
        (("cartao", "credito", "debito"), "Cartão"),
        (("boleto",), "Boleto"),
        (("transferencia", "ted", "doc"), "Transferência"),
    )
    for terms, method in rules:
        if any(term in plain for term in terms):
            return method
    return "Outro"


def _extract_description(question: str, *, fallback: str) -> str:
    match = re.search(r"(?:referente\s+(?:a|ao)|com|por)\s+(.+)", question, flags=re.I)
    description = (match.group(1) if match else fallback).strip(" .,-")
    description = re.sub(r"^r\$?\s*\d+(?:\.\d{3})*(?:,\d{1,2})?\s*", "", description, flags=re.I)
    description = re.sub(r"\b(?:no\s+valor\s+de|valor\s+de)\s+r?\$?\s*\d+(?:\.\d{3})*(?:,\d{1,2})?\b", "", description, flags=re.I)
    description = re.sub(r"\b(?:hoje|ontem)\b", "", description, flags=re.I)
    description = re.sub(r"\b(?:no|via|pelo)\s+(?:pix|cart[aã]o|boleto|dinheiro|transfer[eê]ncia)\b", "", description, flags=re.I)
    description = re.sub(r"\s+", " ", description).strip(" .,-")
    return description[:255] or fallback


def _local_arguments(question: str, action_type: str, today: date) -> dict[str, Any]:
    amount = _parse_amount(question)
    when = _parse_date(question, today).isoformat()
    if action_type in {"transaction", "recurring_transaction"}:
        tx_type = _transaction_type(question)
        plain = _plain(question)
        frequency = "Semanal" if any(term in plain for term in ("semana", "semanal")) else "Anual" if any(term in plain for term in ("ano", "anual")) else "Mensal"
        return {
            "action_type": action_type,
            "tx_type": tx_type,
            "date": when,
            "value": amount,
            "description": _extract_description(
                question,
                fallback="Receita via Assistente" if tx_type == "Receita" else "Despesa via Assistente",
            ),
            "category": _category(question, tx_type),
            "document_number": "",
            "counterparty": "",
            "payment_method": _payment_method(question),
            "invoice_type": "",
            "number": "",
            "customer": "",
            "customer_document": "",
            "status": "",
            "frequency": frequency,
            "end_date": "",
            "title": "",
            "contact_type": "",
            "name": "",
            "email": "",
            "phone": "",
            "notes": "",
        }

    if action_type == "obligation":
        title = re.sub(r"(?i)^.*?\b(?:me lembre|lembrete|obrigação|obrigacao)\b\s*(?:de|para)?\s*", "", question).strip(" .,-")
        return {
            "action_type": "obligation", "date": when, "title": title[:180],
            "category": "Fiscal" if any(term in _plain(question) for term in ("das", "imposto", "fiscal", "declaracao")) else "Administrativo",
            "notes": question.strip()[:500],
        }

    if action_type == "contact":
        plain = _plain(question)
        contact_type = "Fornecedor" if "fornecedor" in plain else "Cliente" if "cliente" in plain else "Contato"
        name_match = re.search(r"(?i)\b(?:cliente|fornecedor|contato)\s+(.+?)(?=\s+(?:cpf|cnpj|e-?mail|telefone|fone)\b|[,.;]|$)", question)
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", question)
        phone_match = re.search(r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}", question)
        document_match = re.search(r"\b(?:\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b", question)
        return {
            "action_type": "contact", "contact_type": contact_type,
            "name": (name_match.group(1) if name_match else "").strip()[:180],
            "document": document_match.group(0) if document_match else "",
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "notes": "Cadastrado via Assistente Razync",
        }

    number_match = re.search(r"\bnota(?:\s+fiscal)?\s*(?:n[ºo.]?|numero)?\s*([A-Za-z0-9./_-]+)", question, flags=re.I)
    customer_match = re.search(r"\bcliente\s+(.+?)(?=\s+(?:no valor|de r\$|por r\$|referente)|[,.;]|$)", question, flags=re.I)
    return {
        "action_type": "invoice",
        "tx_type": "",
        "date": when,
        "value": amount,
        "description": _extract_description(question, fallback="Nota cadastrada via Assistente"),
        "category": "",
        "document_number": "",
        "counterparty": "",
        "payment_method": "",
        "invoice_type": "Venda/Comércio" if "venda" in _plain(question) else "Serviço",
        "number": (number_match.group(1) if number_match else "").strip(),
        "customer": (customer_match.group(1) if customer_match else "").strip()[:180],
        "customer_document": "",
        "status": "Emitida",
    }


_ACTION_TOOL = {
    "type": "function",
    "name": "prepare_razync_action",
    "description": (
        "Prepare, sem executar, um lançamento financeiro ou cadastro de nota pedido explicitamente pelo usuário. "
        "Use strings vazias quando um campo opcional não tiver sido informado. Nunca invente valores, números ou pessoas."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action_type": {"type": "string", "enum": ["transaction", "invoice"]},
            "tx_type": {"type": "string", "enum": ["", "Receita", "Despesa"]},
            "date": {"type": "string", "description": "Data ISO YYYY-MM-DD."},
            "value": {"type": "number", "minimum": 0},
            "description": {"type": "string"},
            "category": {"type": "string", "enum": ["", *TRANSACTION_CATEGORIES]},
            "document_number": {"type": "string"},
            "counterparty": {"type": "string"},
            "payment_method": {"type": "string", "enum": ["", *PAYMENT_METHODS]},
            "invoice_type": {"type": "string", "enum": ["", *INVOICE_TYPES]},
            "number": {"type": "string"},
            "customer": {"type": "string"},
            "customer_document": {"type": "string"},
            "status": {"type": "string", "enum": ["", "Emitida", "Cancelada"]},
        },
        "required": [
            "action_type", "tx_type", "date", "value", "description", "category",
            "document_number", "counterparty", "payment_method", "invoice_type",
            "number", "customer", "customer_document", "status",
        ],
    },
}


def _openai_arguments(question: str, *, api_key: str, model: str, today: date) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key.strip(), timeout=20.0, max_retries=0)
    response = client.responses.create(
        model=model.strip(),
        instructions=(
            "Extraia somente dados explicitamente presentes. A data de hoje é "
            f"{today.isoformat()}. Converta hoje/ontem para ISO. Não execute a ação."
        ),
        input=question.strip(),
        tools=[_ACTION_TOOL],
        tool_choice="required",
        parallel_tool_calls=False,
        store=False,
        max_output_tokens=500,
    )
    for item in response.output:
        if getattr(item, "type", "") == "function_call" and getattr(item, "name", "") == "prepare_razync_action":
            return json.loads(getattr(item, "arguments", "{}") or "{}")
    raise AssistantActionError("A IA não retornou um rascunho estruturado.")


def _safe_date(value: Any, today: date) -> date:
    try:
        parsed = date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return today
    if parsed > today + timedelta(days=366) or parsed < date(2000, 1, 1):
        return today
    return parsed


def _normalize_draft(
    arguments: dict[str, Any],
    *,
    today: date,
    source: str,
    action_key: str = "",
    channel: str = "web",
) -> ActionDraft:
    action_type = str(arguments.get("action_type") or "")
    value = round(max(0.0, float(arguments.get("value") or 0)), 2)
    when = _safe_date(arguments.get("date"), today)

    if action_type == "transaction":
        tx_type = str(arguments.get("tx_type") or "")
        category = str(arguments.get("category") or "Outros")
        payment = str(arguments.get("payment_method") or "Outro")
        description = str(arguments.get("description") or "").strip()[:255]
        payload = {
            "tx_date": when.isoformat(),
            "tx_type": tx_type,
            "description": description,
            "category": category if category in TRANSACTION_CATEGORIES else "Outros",
            "value": value,
            "document_number": str(arguments.get("document_number") or "").strip()[:100],
            "counterparty": str(arguments.get("counterparty") or "").strip()[:180],
            "payment_method": payment if payment in PAYMENT_METHODS else "Outro",
        }
        missing = tuple(
            label for condition, label in (
                (tx_type not in {"Receita", "Despesa"}, "tipo (receita ou despesa)"),
                (value <= 0, "valor"),
                (not description, "descrição"),
            ) if condition
        )
        summary = (
            f"{tx_type or 'Lançamento'} de R$ {value:,.2f} em {when.strftime('%d/%m/%Y')} · "
            f"{payload['category']} · {payload['description'] or 'sem descrição'}"
        )
        return ActionDraft(action_type, payload, missing, summary, source, action_key or uuid4().hex, channel)

    if action_type == "recurring_transaction":
        tx_type = str(arguments.get("tx_type") or "")
        category = str(arguments.get("category") or "Outros")
        payment = str(arguments.get("payment_method") or "Outro")
        frequency = str(arguments.get("frequency") or "Mensal")
        description = str(arguments.get("description") or "").strip()[:255]
        end_date_raw = str(arguments.get("end_date") or "").strip()
        end_date = _safe_date(end_date_raw, today).isoformat() if end_date_raw else None
        payload = {
            "tx_type": tx_type,
            "description": description,
            "category": category if category in TRANSACTION_CATEGORIES else "Outros",
            "value": value,
            "payment_method": payment if payment in PAYMENT_METHODS else "Outro",
            "frequency": frequency if frequency in RECURRENCE_FREQUENCIES else "Mensal",
            "next_date": when.isoformat(),
            "end_date": end_date,
            "active": True,
        }
        missing = tuple(label for condition, label in (
            (tx_type not in {"Receita", "Despesa"}, "tipo (receita ou despesa)"),
            (value <= 0, "valor"), (not description, "descrição"),
        ) if condition)
        summary = f"{tx_type or 'Lançamento'} {payload['frequency'].lower()} de R$ {value:,.2f} · {description or 'sem descrição'}"
        return ActionDraft(action_type, payload, missing, summary, source, action_key or uuid4().hex, channel)

    if action_type == "invoice":
        invoice_type = str(arguments.get("invoice_type") or "Serviço")
        description = str(arguments.get("description") or "").strip()[:255]
        payload = {
            "issue_date": when.isoformat(),
            "invoice_type": invoice_type if invoice_type in INVOICE_TYPES else "Serviço",
            "number": str(arguments.get("number") or "").strip()[:100],
            "customer": str(arguments.get("customer") or "").strip()[:180],
            "customer_document": str(arguments.get("customer_document") or "").strip()[:30],
            "description": description,
            "amount": value,
            "status": str(arguments.get("status") or "Emitida") if str(arguments.get("status") or "Emitida") in {"Emitida", "Cancelada"} else "Emitida",
        }
        missing = tuple(label for condition, label in ((value <= 0, "valor"), (not description, "descrição")) if condition)
        number = payload["number"] or "sem número"
        summary = f"Nota {number} · R$ {value:,.2f} · {when.strftime('%d/%m/%Y')} · {description or 'sem descrição'}"
        return ActionDraft(action_type, payload, missing, summary, source, action_key or uuid4().hex, channel)

    if action_type == "obligation":
        title = str(arguments.get("title") or "").strip()[:180]
        payload = {
            "title": title, "due_date": when.isoformat(), "status": "Pendente",
            "category": str(arguments.get("category") or "Administrativo")[:80],
            "notes": str(arguments.get("notes") or "").strip()[:1000],
        }
        missing = tuple(label for condition, label in ((not title, "título do lembrete"),) if condition)
        return ActionDraft(action_type, payload, missing, f"Lembrete: {title or 'sem título'} · {when.strftime('%d/%m/%Y')}", source, action_key or uuid4().hex, channel)

    if action_type == "contact":
        name = str(arguments.get("name") or "").strip()[:180]
        contact_type = str(arguments.get("contact_type") or "Contato")
        payload = {
            "contact_type": contact_type if contact_type in {"Cliente", "Fornecedor", "Contato"} else "Contato",
            "name": name, "document": str(arguments.get("document") or "").strip()[:30],
            "email": str(arguments.get("email") or "").strip()[:255],
            "phone": str(arguments.get("phone") or "").strip()[:40],
            "notes": str(arguments.get("notes") or "").strip()[:1000],
        }
        missing = ("nome",) if not name else ()
        return ActionDraft(action_type, payload, missing, f"{payload['contact_type']}: {name or 'sem nome'}", source, action_key or uuid4().hex, channel)

    raise AssistantActionError("Tipo de ação não reconhecido.")


def _plan_batch_transactions(question: str, *, today: date, channel: str) -> ActionDraft | None:
    """Prepara listas simples como 'aluguel 900, internet 120 e energia 180'."""
    plain = _plain(question)
    if not _looks_operational(question) or not any(term in plain for term in ("despesa", "receita", "lançamento", "lancamento")):
        return None
    body = question.split(":", 1)[1] if ":" in question else question
    parts = re.split(r"\s*[,;]\s*|\s+e\s+(?=[^,;]*\d)", body, flags=re.I)
    tx_type = _transaction_type(question)
    if tx_type not in {"Receita", "Despesa"}:
        return None

    items: list[dict[str, Any]] = []
    for part in parts:
        amount = _parse_amount(part)
        if amount <= 0:
            continue
        description = re.sub(r"(?i)\br\$\s*\d+(?:\.\d{3})*(?:,\d{1,2})?\b", " ", part)
        description = re.sub(r"\b\d+(?:[.,]\d{1,2})?\b", " ", description)
        description = re.sub(
            r"(?i)\b(?:registre|lance|adicione|inclua|crie|despesas?|receitas?|lançamentos?|lancamentos?|de|uma|um|três|tres|duas|dois)\b",
            " ",
            description,
        )
        description = re.sub(r"\s+", " ", description).strip(" .,-")
        if not description:
            continue
        arguments = _local_arguments(f"{tx_type} de R$ {amount:.2f} com {description}", "transaction", today)
        arguments["tx_type"] = tx_type
        arguments["description"] = description[:255]
        arguments["value"] = amount
        arguments["date"] = _parse_date(question, today).isoformat()
        child = _normalize_draft(arguments, today=today, source="Lista", channel=channel)
        if child.ready:
            items.append(child.to_dict())

    if len(items) < 2:
        return None
    total = sum(float(item["payload"]["value"]) for item in items)
    summary = f"{len(items)} lançamentos de {tx_type.lower()} · total de R$ {total:,.2f}"
    return ActionDraft("batch", {"items": items}, (), summary, "Lista", uuid4().hex, channel)


def plan_assistant_action(
    question: str,
    *,
    api_key: str = "",
    model: str = "gpt-5.4-mini",
    today: date | None = None,
    channel: str = "web",
) -> ActionDraft | None:
    today = today or _business_today()
    safe_channel = "whatsapp" if str(channel).lower() == "whatsapp" else "web"
    batch = _plan_batch_transactions(question, today=today, channel=safe_channel)
    if batch is not None:
        return batch
    intent = _intent(question)
    if intent is None:
        return None

    local_arguments = _local_arguments(question, intent, today)
    if api_key.strip() and intent in {"transaction", "invoice"}:
        try:
            arguments = _openai_arguments(question, api_key=api_key, model=model, today=today)
            if arguments.get("action_type") != intent:
                arguments["action_type"] = intent
            return _normalize_draft(arguments, today=today, source="OpenAI", channel=safe_channel)
        except Exception:
            pass
    return _normalize_draft(local_arguments, today=today, source="Local", channel=safe_channel)


def revise_action_draft(draft: dict[str, Any], updates: dict[str, Any] | None = None, *, today: date | None = None) -> ActionDraft:
    """Revalidate user-edited fields instead of trusting values stored in session state."""
    today = today or _business_today()
    action_type = str(draft.get("action_type") or "")
    payload = {**dict(draft.get("payload") or {}), **dict(updates or {})}
    arguments = {"action_type": action_type, **payload}
    if action_type == "transaction":
        arguments["date"] = payload.get("tx_date")
    elif action_type == "invoice":
        arguments["date"] = payload.get("issue_date")
        arguments["value"] = payload.get("amount")
    elif action_type == "recurring_transaction":
        arguments["date"] = payload.get("next_date")
    elif action_type == "obligation":
        arguments["date"] = payload.get("due_date")
    return _normalize_draft(
        arguments,
        today=today,
        source="Revisado pelo usuário",
        action_key=str(draft.get("action_key") or ""),
        channel=str(draft.get("channel") or "web"),
    )


def plan_document_action(analysis: dict[str, Any], filename: str, *, today: date | None = None) -> ActionDraft | None:
    """Turn locally extracted document metadata into a confirmable draft."""
    today = today or _business_today()
    amount = float(analysis.get("value") or 0)
    number = str(analysis.get("document_number") or "")
    category = str(analysis.get("category") or "Outro")
    if category == "Nota Fiscal":
        return _normalize_draft({
            "action_type": "invoice", "date": today.isoformat(), "value": amount,
            "number": number, "description": f"Nota importada de {filename}",
            "invoice_type": "Serviço", "customer": "", "customer_document": "", "status": "Emitida",
        }, today=today, source="Documento")
    if category in {"Comprovante", "DAS"} and amount > 0:
        return _normalize_draft({
            "action_type": "transaction", "date": today.isoformat(), "value": amount,
            "tx_type": "Despesa", "description": f"{category} · {filename}",
            "category": "Taxas" if category == "DAS" else "Outros",
            "document_number": number, "counterparty": "", "payment_method": "Outro",
        }, today=today, source="Documento")
    return None


def _action_receipt(*, message: str, action_type: str, record_id: int | None, summary: str, action_key: str = "") -> dict[str, Any]:
    routes = {
        "transaction": "Movimentações",
        "invoice": "Notas Fiscais",
        "recurring_transaction": "Recorrências",
        "obligation": "Obrigações",
        "contact": "Clientes e Fornecedores",
        "batch": "Movimentações",
    }
    return {
        "message": message,
        "action_type": action_type,
        "record_id": record_id,
        "summary": summary,
        "route": routes.get(action_type, "Dashboard"),
        "action_key": action_key,
    }


def _execute_one(user_id: int, draft: dict[str, Any]) -> dict[str, Any]:
    from database import (
        add_contact, add_invoice, add_obligation, add_recurring_transaction, add_transaction,
        list_contacts, list_invoices, list_obligations, list_recurring_transactions, list_transactions,
    )

    action_type = str(draft.get("action_type") or "")
    payload = dict(draft.get("payload") or {})
    action_key = str(draft.get("action_key") or "")
    if draft.get("missing_fields"):
        raise AssistantActionError("A ação ainda possui campos obrigatórios pendentes.")

    if action_type == "transaction":
        normalized = _normalize_draft({"action_type": action_type, **payload, "date": payload.get("tx_date")}, today=_business_today(), source="validated", action_key=action_key)
        if not normalized.ready:
            raise AssistantActionError("Confira os dados do lançamento antes de salvar.")
        safe = normalized.payload
        safe["tx_date"] = date.fromisoformat(safe["tx_date"])
        before = {int(row["id"]) for row in list_transactions(int(user_id))}
        add_transaction(int(user_id), **safe)
        record_id = next((int(row["id"]) for row in list_transactions(int(user_id)) if int(row["id"]) not in before), None)
        return _action_receipt(message="Lançamento salvo e financeiro atualizado.", action_type=action_type, record_id=record_id, summary=normalized.summary, action_key=action_key)

    if action_type == "invoice":
        normalized = _normalize_draft({"action_type": action_type, "date": payload.get("issue_date"), "value": payload.get("amount"), **payload}, today=_business_today(), source="validated", action_key=action_key)
        if not normalized.ready:
            raise AssistantActionError("Confira os dados da nota antes de salvar.")
        safe = normalized.payload
        safe["issue_date"] = date.fromisoformat(safe["issue_date"])
        before = {int(row["id"]) for row in list_invoices(int(user_id))}
        add_invoice(int(user_id), **safe)
        record_id = next((int(row["id"]) for row in list_invoices(int(user_id)) if int(row["id"]) not in before), None)
        return _action_receipt(message="Nota cadastrada no Razync. A emissão oficial continua no portal municipal.", action_type=action_type, record_id=record_id, summary=normalized.summary, action_key=action_key)

    if action_type == "recurring_transaction":
        normalized = revise_action_draft(draft)
        if not normalized.ready:
            raise AssistantActionError("Confira os dados da recorrência antes de salvar.")
        safe = normalized.payload
        safe["next_date"] = date.fromisoformat(safe["next_date"])
        safe["end_date"] = date.fromisoformat(safe["end_date"]) if safe.get("end_date") else None
        before = {int(row["id"]) for row in list_recurring_transactions(int(user_id))}
        add_recurring_transaction(int(user_id), **safe)
        record_id = next((int(row["id"]) for row in list_recurring_transactions(int(user_id)) if int(row["id"]) not in before), None)
        return _action_receipt(message="Automação recorrente criada.", action_type=action_type, record_id=record_id, summary=normalized.summary, action_key=action_key)

    if action_type == "obligation":
        normalized = revise_action_draft(draft)
        if not normalized.ready:
            raise AssistantActionError("Confira o lembrete antes de salvar.")
        safe = normalized.payload
        safe["due_date"] = date.fromisoformat(safe["due_date"])
        before = {int(row["id"]) for row in list_obligations(int(user_id))}
        add_obligation(int(user_id), **safe)
        record_id = next((int(row["id"]) for row in list_obligations(int(user_id)) if int(row["id"]) not in before), None)
        return _action_receipt(message="Lembrete salvo na agenda.", action_type=action_type, record_id=record_id, summary=normalized.summary, action_key=action_key)

    if action_type == "contact":
        normalized = revise_action_draft(draft)
        if not normalized.ready:
            raise AssistantActionError("Informe o nome do contato antes de salvar.")
        before = {int(row["id"]) for row in list_contacts(int(user_id))}
        add_contact(int(user_id), **normalized.payload)
        record_id = next((int(row["id"]) for row in list_contacts(int(user_id)) if int(row["id"]) not in before), None)
        return _action_receipt(message="Contato cadastrado com sucesso.", action_type=action_type, record_id=record_id, summary=normalized.summary, action_key=action_key)

    raise AssistantActionError("Ação não suportada pelo Assistente.")


def execute_assistant_action(user_id: int, draft: dict[str, Any], *, return_receipt: bool = False) -> str | dict[str, Any]:
    from assistant_action_store import AssistantActionStoreError, claim_action, complete_action, fail_action

    action_type = str(draft.get("action_type") or "")
    action_key = str(draft.get("action_key") or "")
    channel = str(draft.get("channel") or "web")
    summary = str(draft.get("summary") or "Ação preparada pela IA")
    if draft.get("missing_fields"):
        raise AssistantActionError("A ação ainda possui campos obrigatórios pendentes.")

    claimed = True
    previous = None
    if action_key:
        try:
            claimed, previous = claim_action(
                user_id, action_key, action_type=action_type, channel=channel, summary=summary,
            )
        except AssistantActionStoreError as exc:
            raise AssistantActionError(str(exc)) from exc
        if not claimed:
            if previous:
                previous = dict(previous)
                previous["duplicate"] = True
                previous["message"] = "Esta ação já havia sido salva. Nenhum registro duplicado foi criado."
                return previous if return_receipt else previous["message"]
            raise AssistantActionError("Esta ação já está sendo processada. Aguarde alguns instantes.")

    created: list[dict[str, Any]] = []
    try:
        if action_type == "batch":
            items = list(dict(draft.get("payload") or {}).get("items") or [])
            if len(items) < 2 or len(items) > 20:
                raise AssistantActionError("A lista deve conter entre 2 e 20 lançamentos.")
            for item in items:
                created.append(_execute_one(int(user_id), dict(item)))
            receipt = _action_receipt(
                message=f"{len(created)} lançamentos salvos e financeiro atualizado.",
                action_type="batch", record_id=None, summary=summary, action_key=action_key,
            )
            receipt["items"] = created
        else:
            receipt = _execute_one(int(user_id), draft)
        if action_key:
            try:
                complete_action(user_id, action_key, receipt)
            except AssistantActionStoreError:
                receipt["warning"] = "A ação foi salva, mas o histórico ficará disponível após a próxima sincronização."
    except AssistantActionError as exc:
        for item in reversed(created):
            try:
                undo_assistant_action(user_id, item)
            except AssistantActionError:
                pass
        if action_key:
            fail_action(user_id, action_key, str(exc))
        raise
    except Exception as exc:
        for item in reversed(created):
            try:
                undo_assistant_action(user_id, item)
            except AssistantActionError:
                pass
        if action_key:
            fail_action(user_id, action_key, "Falha ao salvar")
        raise AssistantActionError("Não foi possível salvar a ação agora.") from exc
    return receipt if return_receipt else str(receipt["message"])


def undo_assistant_action(user_id: int, receipt: dict[str, Any]) -> str:
    """Undo only the exact record created by the latest confirmed assistant action."""
    from database import delete_contact, delete_invoice, delete_obligation, delete_recurring_transaction, delete_transaction

    action_type = str(receipt.get("action_type") or "")
    if action_type == "batch":
        items = list(receipt.get("items") or [])
        if not items:
            raise AssistantActionError("Não foi possível identificar os lançamentos para desfazer.")
        for item in reversed(items):
            undo_assistant_action(user_id, dict(item))
        try:
            from assistant_action_store import mark_action_undone
            mark_action_undone(user_id, str(receipt.get("action_key") or ""))
        except Exception:
            pass
        return f"{len(items)} lançamentos da IA foram desfeitos com segurança."

    record_id = receipt.get("record_id")
    if not record_id:
        raise AssistantActionError("Não foi possível identificar o item para desfazer.")
    handlers = {
        "transaction": delete_transaction,
        "invoice": delete_invoice,
        "recurring_transaction": delete_recurring_transaction,
        "obligation": delete_obligation,
        "contact": delete_contact,
    }
    handler = handlers.get(action_type)
    if handler is None:
        raise AssistantActionError("Esta ação não pode ser desfeita automaticamente.")
    try:
        handler(int(user_id), int(record_id))
    except Exception as exc:
        raise AssistantActionError("Não foi possível desfazer a última ação.") from exc
    try:
        from assistant_action_store import mark_action_undone
        mark_action_undone(user_id, str(receipt.get("action_key") or ""))
    except Exception:
        pass
    return "Última ação da IA desfeita com segurança."

