from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any

from openai import OpenAI


TRANSACTION_CATEGORIES = (
    "Serviços", "Vendas", "Materiais", "Aluguel", "Transporte",
    "Taxas", "Marketing", "Pró-labore/Retirada", "Outros",
)
PAYMENT_METHODS = ("PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro")
INVOICE_TYPES = ("Serviço", "Venda/Comércio")
_ACTION_VERBS = (
    "adicione", "adicionar", "anote", "anotar", "cadastre", "cadastrar",
    "inclua", "incluir", "lance", "lançar", "registre", "registrar",
    "gastei", "paguei", "comprei", "recebi", "vendi",
)
_GUIDANCE_PREFIXES = ("como ", "onde ", "posso ", "quero saber", "me explique", "qual ")


@dataclass(frozen=True)
class ActionDraft:
    action_type: str
    payload: dict[str, Any]
    missing_fields: tuple[str, ...]
    summary: str
    source: str = "local"

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
    if re.search(r"\b(nota fiscal|nfse|nfs-e|nota\s+(?:n[ºo.]?\s*)?\w+)", text):
        return "invoice"
    if any(term in text for term in ("receita", "despesa", "gastei", "paguei", "comprei", "recebi", "vendi", "entrada", "saida")):
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
    if any(term in plain for term in ("despesa", "gastei", "paguei", "comprei", "saida")):
        return "Despesa"
    if any(term in plain for term in ("receita", "recebi", "vendi", "entrada")):
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
    match = re.search(r"(?:referente\s+(?:a|ao)|por|de)\s+(.+)", question, flags=re.I)
    description = (match.group(1) if match else fallback).strip(" .,-")
    description = re.sub(r"\b(?:hoje|ontem)\b", "", description, flags=re.I)
    description = re.sub(r"\b(?:no|via|pelo)\s+(?:pix|cart[aã]o|boleto|dinheiro|transfer[eê]ncia)\b", "", description, flags=re.I)
    description = re.sub(r"\s+", " ", description).strip(" .,-")
    return description[:255] or fallback


def _local_arguments(question: str, action_type: str, today: date) -> dict[str, Any]:
    amount = _parse_amount(question)
    when = _parse_date(question, today).isoformat()
    if action_type == "transaction":
        tx_type = _transaction_type(question)
        return {
            "action_type": "transaction",
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


def _normalize_draft(arguments: dict[str, Any], *, today: date, source: str) -> ActionDraft:
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
        return ActionDraft(action_type, payload, missing, summary, source)

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
        return ActionDraft(action_type, payload, missing, summary, source)

    raise AssistantActionError("Tipo de ação não reconhecido.")


def plan_assistant_action(
    question: str,
    *,
    api_key: str = "",
    model: str = "gpt-5.4-mini",
    today: date | None = None,
) -> ActionDraft | None:
    today = today or date.today()
    intent = _intent(question)
    if intent is None:
        return None

    local_arguments = _local_arguments(question, intent, today)
    if api_key.strip():
        try:
            arguments = _openai_arguments(question, api_key=api_key, model=model, today=today)
            if arguments.get("action_type") != intent:
                arguments["action_type"] = intent
            return _normalize_draft(arguments, today=today, source="OpenAI")
        except Exception:
            pass
    return _normalize_draft(local_arguments, today=today, source="Local")


def execute_assistant_action(user_id: int, draft: dict[str, Any]) -> str:
    from database import add_invoice, add_transaction

    action_type = str(draft.get("action_type") or "")
    payload = dict(draft.get("payload") or {})
    if draft.get("missing_fields"):
        raise AssistantActionError("A ação ainda possui campos obrigatórios pendentes.")

    try:
        if action_type == "transaction":
            normalized = _normalize_draft({"action_type": action_type, **payload, "date": payload.get("tx_date")}, today=date.today(), source="validated")
            if not normalized.ready:
                raise AssistantActionError("Confira os dados do lançamento antes de salvar.")
            safe = normalized.payload
            safe["tx_date"] = date.fromisoformat(safe["tx_date"])
            add_transaction(int(user_id), **safe)
            return "Lançamento salvo. O Dashboard e os relatórios já serão atualizados."

        if action_type == "invoice":
            normalized = _normalize_draft({
                "action_type": action_type,
                "date": payload.get("issue_date"),
                "value": payload.get("amount"),
                **payload,
            }, today=date.today(), source="validated")
            if not normalized.ready:
                raise AssistantActionError("Confira os dados da nota antes de salvar.")
            safe = normalized.payload
            safe["issue_date"] = date.fromisoformat(safe["issue_date"])
            add_invoice(int(user_id), **safe)
            return "Nota cadastrada no Razync. Isso não emite a NFS-e no portal oficial."

        raise AssistantActionError("Ação não suportada pelo Assistente.")
    except AssistantActionError:
        raise
    except Exception as exc:
        raise AssistantActionError("Não foi possível salvar a ação agora.") from exc
