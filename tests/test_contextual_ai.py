from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from contextual_ai import open_assistant_with_context


def test_handoff_prepares_question_and_context_without_mutation():
    navigate = Mock()
    session = {}
    with patch("contextual_ai.st.session_state", session), patch("contextual_ai.st.rerun") as rerun:
        open_assistant_with_context(
            navigate=navigate,
            source="finance_workspace",
            title="Teste",
            question="Analise meu mês",
            detail="Resumo seguro",
            page="Financeiro",
        )
    assert session["razync_ai_pending_question"] == "Analise meu mês"
    assert session["razync_ai_pending_context"]["source"] == "finance_workspace"
    assert session["razync_floating_open"] is True
    navigate.assert_not_called()
    rerun.assert_called_once()


def test_finance_and_fiscal_have_contextual_ai_actions():
    finance = Path("finance_workspace.py").read_text(encoding="utf-8")
    fiscal = Path("fiscal_workspace.py").read_text(encoding="utf-8")
    assert "contextual_ai_button(" in finance
    assert "Analisar este mês" in finance
    assert "Revisar despesas" in finance
    assert "contextual_ai_button(" in fiscal
    assert "Revisar rotina fiscal" in fiscal
    assert "Entender limite do MEI" in fiscal


def test_contextual_handoff_never_calls_data_mutation_helpers():
    source = Path("contextual_ai.py").read_text(encoding="utf-8")
    for forbidden in ("delete_", "update_", "insert_", "save_", "execute_assistant_action"):
        assert forbidden not in source
