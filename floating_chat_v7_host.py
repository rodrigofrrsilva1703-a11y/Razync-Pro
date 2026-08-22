from __future__ import annotations

import streamlit as st

from assistant_actions import AssistantActionError, execute_assistant_action
from assistant_workspace import (
    _append_message,
    _answer_question,
    _ensure_messages,
    _prepare_resources,
    _session_snapshot,
    _store_turn,
)
from components.razync_chat import razync_chat

_LAST_EVENT_KEY = "razync_chat_v7_last_event"
_OPEN_KEY = "razync_floating_open"

_QUICK_ACTIONS = [
    {"label": "Despesa", "prompt": "Quero registrar uma despesa"},
    {"label": "Receita", "prompt": "Quero registrar uma receita"},
    {"label": "Nota", "prompt": "Quero cadastrar uma nota fiscal"},
    {"label": "Lembrete", "prompt": "Quero criar um lembrete"},
]


def _public_messages(messages: list[dict]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for message in messages[-30:]:
        role = "user" if str(message.get("role") or "assistant") == "user" else "assistant"
        content = str(message.get("content") or "").strip()
        if content:
            cleaned.append({"role": role, "content": content})
    return cleaned


def _pending_action_card(draft: object) -> dict | None:
    """Converte o rascunho interno em dados seguros para o componente visual."""
    if not isinstance(draft, dict):
        return None

    missing = [str(item) for item in draft.get("missing_fields") or [] if str(item).strip()]
    labels = {
        "transaction": "Lançamento preparado",
        "recurring_transaction": "Automação preparada",
        "invoice": "Nota preparada",
        "obligation": "Lembrete preparado",
        "contact": "Contato preparado",
    }
    action_type = str(draft.get("action_type") or "")
    return {
        "title": labels.get(action_type, "Ação preparada"),
        "summary": str(draft.get("summary") or "Confira os dados antes de continuar."),
        "missing": missing,
        "ready": not missing and bool(draft.get("ready", True)),
    }


def _finish_pending_action(*, user_id: int, confirm: bool) -> None:
    draft = st.session_state.get("razync_ai_pending_action")
    if not isinstance(draft, dict):
        return

    if not confirm:
        st.session_state.pop("razync_ai_pending_action", None)
        _append_message(
            "assistant",
            "Ação cancelada. Nenhum dado foi alterado.",
            metadata={"event": "action_cancelled"},
        )
        st.rerun()
        return

    try:
        receipt = execute_assistant_action(user_id, draft, return_receipt=True)
    except AssistantActionError as exc:
        _append_message("assistant", str(exc), metadata={"event": "action_error"})
        st.rerun()
        return

    message = str(receipt.get("message") or "Ação concluída.") if isinstance(receipt, dict) else str(receipt)
    if isinstance(receipt, dict):
        st.session_state["razync_ai_last_receipt"] = receipt
    st.session_state.pop("razync_ai_pending_action", None)
    st.session_state.pop("razync_ai_last_resources", None)
    _append_message("assistant", message, metadata={"event": "action_confirmed"})
    st.rerun()


def render_isolated_chat_v7(*, user: dict, page: str, navigate) -> None:
    """Renderiza o chat V7 usando um Custom Component isolado."""
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
        messages=_public_messages(messages),
        quick_actions=_QUICK_ACTIONS,
        action_card=_pending_action_card(st.session_state.get("razync_ai_pending_action")),
        is_loading=False,
        theme=theme,
        key="razync_chat_v7_instance",
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
    if action == "review_action":
        st.session_state[_OPEN_KEY] = False
        navigate("Assistente Razync")
        return
    if action not in {"send", "quick_prompt"}:
        return

    question = str(event.get("text") or "").strip()
    if not question:
        return

    result = _answer_question(
        question,
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        annual_limit=annual_limit,
        current_year=current_year,
        current_page=page,
    )
    resources = _prepare_resources(
        question,
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        current_year=current_year,
    )
    _store_turn(question, result["answer"], resources)
    st.session_state["razync_ai_flash_notices"] = result["notices"]
    st.rerun()

