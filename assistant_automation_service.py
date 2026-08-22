from __future__ import annotations

from datetime import date
from typing import Any

from assistant_actions import (
    ActionDraft,
    execute_assistant_action,
    plan_assistant_action,
    revise_action_draft,
    undo_assistant_action,
)


def prepare_automation(
    text: str,
    *,
    channel: str = "web",
    api_key: str = "",
    model: str = "gpt-5.4-mini",
    today: date | None = None,
) -> ActionDraft | None:
    """Entrada compartilhada para web e futuro adaptador oficial do WhatsApp."""
    return plan_assistant_action(text, channel=channel, api_key=api_key, model=model, today=today)


def revise_automation(draft: dict[str, Any], updates: dict[str, Any]) -> ActionDraft:
    return revise_action_draft(draft, updates)


def confirm_automation(user_id: int, draft: dict[str, Any], *, return_receipt: bool = True) -> dict[str, Any] | str:
    receipt = execute_assistant_action(user_id, draft, return_receipt=True)
    if not isinstance(receipt, dict):
        normalized = {"message": str(receipt), "action_type": str(draft.get("action_type") or "")}
    else:
        normalized = receipt
    return normalized if return_receipt else str(normalized.get("message") or "Ação concluída.")


def undo_automation(user_id: int, receipt: dict[str, Any]) -> str:
    return undo_assistant_action(user_id, receipt)

