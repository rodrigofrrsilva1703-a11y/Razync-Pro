from pathlib import Path


def test_dashboard_exposes_ai_command_and_quick_business_actions():
    source = Path("dashboard_workspace.py").read_text(encoding="utf-8")
    assert "dashboard_ai_command" in source
    assert "razync_ai_pending_question" in source
    assert "Registrar receita" in source
    assert "Registrar despesa" in source
    assert "Variação em relação ao mês anterior" in source


def test_finance_chart_uses_business_labels_and_semantic_colors():
    source = Path("finance_workspace.py").read_text(encoding="utf-8")
    assert '"Valor (R$)"' in source
    assert 'tokens(theme)["success"]' in source
    assert 'tokens(theme)["danger"]' in source
    assert "hovertemplate" in source


def test_fiscal_workspace_keeps_full_history_while_adding_status_pills():
    source = Path("fiscal_workspace.py").read_text(encoding="utf-8")
    assert "rz-status-table" in source
    assert "_status_tone" in source
    assert "Ver histórico completo do DAS" in source
    assert "st.dataframe" in source


def test_assistant_suggestions_are_visible_at_conversation_start():
    source = Path("assistant_workspace.py").read_text(encoding="utf-8")
    assert "Comece com uma tarefa" in source
    assert "len(messages) <= 1" in source

