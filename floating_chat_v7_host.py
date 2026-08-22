from __future__ import annotations

import base64
import binascii
from pathlib import Path

import streamlit as st

from assistant_actions import (
    AssistantActionError, INVOICE_TYPES, PAYMENT_METHODS, RECURRENCE_FREQUENCIES,
    TRANSACTION_CATEGORIES, plan_document_action,
)
from assistant_audio import AssistantAudioError, MAX_AUDIO_BYTES, transcribe_audio
from assistant_automation_service import confirm_automation, revise_automation, undo_automation
from assistant_workspace import (
    _append_message, _answer_question, _ensure_messages, _prepare_resources,
    _provider_state, _session_snapshot, _store_turn,
)
from components.razync_chat import razync_chat
from document_intelligence import analyze_document

_LAST_EVENT_KEY = "razync_chat_v7_last_event"
_OPEN_KEY = "razync_floating_open"
_MAX_DOCUMENT_BYTES = 6 * 1024 * 1024
_DOCUMENT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def _public_messages(messages: list[dict]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for message in messages[-30:]:
        role = "user" if str(message.get("role") or "assistant") == "user" else "assistant"
        content = str(message.get("content") or "").strip()
        if content:
            cleaned.append({"role": role, "content": content})
    return cleaned


def _field(key: str, label: str, value, *, field_type: str = "text", options=()) -> dict:
    return {"key": key, "label": label, "value": value if value is not None else "", "type": field_type, "options": list(options)}


def _action_fields(action_type: str, payload: dict) -> list[dict]:
    if action_type in {"transaction", "recurring_transaction"}:
        date_key = "tx_date" if action_type == "transaction" else "next_date"
        fields = [
            _field("tx_type", "Tipo", payload.get("tx_type"), field_type="select", options=("Receita", "Despesa")),
            _field("description", "Descrição", payload.get("description")),
            _field("value", "Valor", payload.get("value"), field_type="number"),
            _field("category", "Categoria", payload.get("category"), field_type="select", options=TRANSACTION_CATEGORIES),
            _field("payment_method", "Pagamento", payload.get("payment_method"), field_type="select", options=PAYMENT_METHODS),
            _field(date_key, "Data", payload.get(date_key), field_type="date"),
        ]
        if action_type == "recurring_transaction":
            fields.append(_field("frequency", "Frequência", payload.get("frequency"), field_type="select", options=RECURRENCE_FREQUENCIES))
        return fields
    if action_type == "invoice":
        return [
            _field("number", "Número", payload.get("number")), _field("customer", "Cliente", payload.get("customer")),
            _field("description", "Descrição", payload.get("description")), _field("amount", "Valor", payload.get("amount"), field_type="number"),
            _field("invoice_type", "Tipo", payload.get("invoice_type"), field_type="select", options=INVOICE_TYPES),
            _field("issue_date", "Data", payload.get("issue_date"), field_type="date"),
        ]
    if action_type == "obligation":
        return [_field("title", "Lembrete", payload.get("title")), _field("due_date", "Vencimento", payload.get("due_date"), field_type="date"), _field("category", "Categoria", payload.get("category"))]
    if action_type == "contact":
        return [
            _field("contact_type", "Tipo", payload.get("contact_type"), field_type="select", options=("Cliente", "Fornecedor", "Contato")),
            _field("name", "Nome", payload.get("name")), _field("document", "CPF ou CNPJ", payload.get("document")),
            _field("email", "E-mail", payload.get("email"), field_type="email"), _field("phone", "Telefone", payload.get("phone")),
        ]
    return []


def _pending_action_card(draft: object) -> dict | None:
    if not isinstance(draft, dict):
        return None
    missing = [str(item) for item in draft.get("missing_fields") or [] if str(item).strip()]
    labels = {
        "transaction": "Lançamento preparado", "recurring_transaction": "Automação preparada",
        "invoice": "Nota preparada", "obligation": "Lembrete preparado",
        "contact": "Contato preparado", "batch": "Lançamentos preparados",
    }
    action_type = str(draft.get("action_type") or "")
    return {
        "title": labels.get(action_type, "Ação preparada"),
        "summary": str(draft.get("summary") or "Confira os dados antes de continuar."),
        "missing": missing, "ready": not missing and bool(draft.get("ready", True)),
        "fields": _action_fields(action_type, dict(draft.get("payload") or {})),
    }


def _receipt_card(receipt: object) -> dict | None:
    if not isinstance(receipt, dict):
        return None
    return {
        "title": "Ação concluída", "summary": str(receipt.get("summary") or receipt.get("message") or "Alteração salva."),
        "message": str(receipt.get("message") or "Alteração salva."), "route_label": "Abrir registro",
        "can_open": bool(receipt.get("route")), "can_undo": not bool(receipt.get("duplicate")),
    }


def _contextual_quick_actions(transactions, invoices, das_rows: list[dict], obligations: list[dict]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if any(str(row.get("status") or "").lower() == "pendente" for row in das_rows):
        actions.append({"label": "Ver DAS", "prompt": "Quais DAS estão pendentes?"})
    if any(str(row.get("status") or "").lower() == "pendente" for row in obligations):
        actions.append({"label": "Prazos", "prompt": "Quais são meus próximos prazos?"})
    if not transactions.empty:
        actions.append({"label": "Analisar mês", "prompt": "Analise minhas receitas e despesas deste mês"})
    if not invoices.empty:
        actions.append({"label": "Notas", "prompt": "Mostre a situação das minhas notas fiscais"})
    defaults = [
        {"label": "Despesa", "prompt": "Quero registrar uma despesa"}, {"label": "Receita", "prompt": "Quero registrar uma receita"},
        {"label": "Nota", "prompt": "Quero cadastrar uma nota fiscal"}, {"label": "Lembrete", "prompt": "Quero criar um lembrete"},
    ]
    for item in defaults:
        if len(actions) >= 4:
            break
        actions.append(item)
    return actions[:4]


def _decode_file_event(event: dict, *, max_bytes: int) -> tuple[bytes, str, str]:
    filename = Path(str(event.get("filename") or "arquivo")).name[:180]
    mime_type = str(event.get("mime_type") or "application/octet-stream")[:100]
    encoded = str(event.get("data") or "")
    if "," in encoded:
        encoded = encoded.split(",", 1)[1]
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Arquivo inválido.") from exc
    if not content or len(content) > max_bytes:
        raise ValueError(f"Envie um arquivo válido de até {max_bytes // (1024 * 1024)} MB.")
    return content, filename, mime_type


def _normalize_updates(values: object) -> dict:
    if not isinstance(values, dict):
        return {}
    updates = {str(key): value for key, value in values.items()}
    for key in ("value", "amount"):
        if key in updates:
            raw = str(updates[key] or "0").strip()
            raw = raw.replace(".", "").replace(",", ".") if "," in raw else raw
            try:
                updates[key] = float(raw)
            except ValueError:
                updates[key] = 0.0
    return updates


def _finish_pending_action(*, user_id: int, confirm: bool) -> None:
    draft = st.session_state.get("razync_ai_pending_action")
    if not isinstance(draft, dict):
        return
    if not confirm:
        st.session_state.pop("razync_ai_pending_action", None)
        _append_message("assistant", "Ação cancelada. Nenhum dado foi alterado.", metadata={"event": "action_cancelled"})
        st.rerun()
        return
    try:
        receipt = confirm_automation(user_id, draft)
    except AssistantActionError as exc:
        _append_message("assistant", str(exc), metadata={"event": "action_error"})
        st.rerun()
        return
    st.session_state["razync_ai_last_receipt"] = receipt
    st.session_state.pop("razync_ai_pending_action", None)
    st.session_state.pop("razync_ai_last_resources", None)
    _append_message("assistant", str(receipt.get("message") or "Ação concluída."), metadata={"event": "action_confirmed"})
    st.rerun()


def _process_question(question: str, *, snapshot: tuple, page: str) -> None:
    profile, transactions, invoices, das_rows, obligations, documents, annual_limit, current_year = snapshot
    result = _answer_question(
        question, profile=profile, transactions=transactions, invoices=invoices, das_rows=das_rows,
        obligations=obligations, documents=documents, annual_limit=annual_limit,
        current_year=current_year, current_page=page,
    )
    resources = _prepare_resources(
        question, profile=profile, transactions=transactions, invoices=invoices, das_rows=das_rows,
        obligations=obligations, documents=documents, current_year=current_year,
    )
    _store_turn(question, result["answer"], resources)
    st.session_state["razync_ai_flash_notices"] = result["notices"]
    st.rerun()


def render_isolated_chat_v7(*, user: dict, page: str, navigate) -> None:
    try:
        user_id = int(user.get("id"))
    except (TypeError, ValueError):
        return
    snapshot = _session_snapshot(user_id)
    if snapshot is None:
        return
    profile, transactions, invoices, das_rows, obligations, documents, annual_limit, current_year = snapshot
    messages = _ensure_messages()
    theme = "dark" if str(st.session_state.get("ui_theme") or "").lower().startswith("esc") else "light"
    event = razync_chat(
        messages=_public_messages(messages), quick_actions=_contextual_quick_actions(transactions, invoices, das_rows, obligations),
        action_card=_pending_action_card(st.session_state.get("razync_ai_pending_action")),
        receipt_card=_receipt_card(st.session_state.get("razync_ai_last_receipt")),
        is_loading=False, theme=theme, key="razync_chat_v7_instance",
    )
    if not isinstance(event, dict):
        return
    event_id = str(event.get("event_id") or "").strip()
    if event_id and event_id == str(st.session_state.get(_LAST_EVENT_KEY) or ""):
        return
    if event_id:
        st.session_state[_LAST_EVENT_KEY] = event_id
    action = str(event.get("action") or "").strip().lower()
    if action == "open_full":
        st.session_state[_OPEN_KEY] = False
        navigate("Assistente Razync")
        return
    if action == "close":
        st.session_state[_OPEN_KEY] = False
        st.rerun()
    if action == "confirm_action":
        _finish_pending_action(user_id=user_id, confirm=True)
        return
    if action == "cancel_action":
        _finish_pending_action(user_id=user_id, confirm=False)
        return
    if action == "update_action":
        draft = st.session_state.get("razync_ai_pending_action")
        if isinstance(draft, dict):
            try:
                revised = revise_automation(draft, _normalize_updates(event.get("values")))
            except AssistantActionError as exc:
                _append_message("assistant", str(exc), metadata={"event": "action_error"})
            else:
                state = revised.to_dict()
                state["original_request"] = draft.get("original_request", "")
                st.session_state["razync_ai_pending_action"] = state
        st.rerun()
    if action == "open_receipt":
        receipt = st.session_state.get("razync_ai_last_receipt")
        if isinstance(receipt, dict) and receipt.get("route"):
            st.session_state[_OPEN_KEY] = False
            navigate(str(receipt["route"]))
        return
    if action == "undo_action":
        receipt = st.session_state.get("razync_ai_last_receipt")
        if isinstance(receipt, dict):
            try:
                message = undo_automation(user_id, receipt)
            except AssistantActionError as exc:
                message = str(exc)
            else:
                st.session_state.pop("razync_ai_last_receipt", None)
            _append_message("assistant", message, metadata={"event": "action_undone"})
        st.rerun()
    if action == "upload_document":
        try:
            content, filename, mime_type = _decode_file_event(event, max_bytes=_MAX_DOCUMENT_BYTES)
            if Path(filename).suffix.lower() not in _DOCUMENT_SUFFIXES:
                raise ValueError("Use PDF, PNG, JPG ou WEBP.")
            analysis = analyze_document(content, mime_type, filename)
            draft = plan_document_action(analysis, filename)
            if draft is None:
                raise ValueError("Não encontrei dados suficientes. Tente uma imagem mais nítida.")
        except (ValueError, OSError) as exc:
            _append_message("assistant", str(exc), metadata={"event": "document_error"})
        except Exception:
            _append_message("assistant", "Não foi possível analisar este documento.", metadata={"event": "document_error"})
        else:
            state = draft.to_dict()
            state["original_request"] = f"Documento {filename}"
            st.session_state["razync_ai_pending_action"] = state
            _append_message("assistant", f"Li {filename} e preparei uma ação. Confira os dados antes de salvar.", metadata={"event": "document_ready"})
        st.rerun()
    if action == "upload_audio":
        try:
            content, filename, _ = _decode_file_event(event, max_bytes=MAX_AUDIO_BYTES)
            provider = _provider_state()
            transcript = transcribe_audio(content, filename, api_key=str(provider.get("openai_api_key") or ""))
        except (ValueError, AssistantAudioError) as exc:
            _append_message("assistant", str(exc), metadata={"event": "audio_error"})
            st.rerun()
            return
        _process_question(transcript, snapshot=snapshot, page=page)
        return
    if action not in {"send", "quick_prompt"}:
        return
    question = str(event.get("text") or "").strip()
    if question:
        _process_question(question, snapshot=snapshot, page=page)

