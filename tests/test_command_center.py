from __future__ import annotations

from pathlib import Path

from command_center import search_commands


def test_search_finds_tools_by_plain_language():
    assert search_commands("das")[0][0] == "DAS"
    assert any(page == "Documentos" for page, _label, _keywords in search_commands("arquivo pdf"))
    assert any(page == "Movimentações" for page, _label, _keywords in search_commands("nova despesa"))


def test_search_is_accent_insensitive():
    results = search_commands("analise financeira")
    assert any(page == "Análise Financeira" for page, _label, _keywords in results)


def test_sidebar_integrates_global_command_center():
    source = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    assert "from command_center import render_command_center" in source
    assert "render_command_center(navigate=navigate, current_page=page)" in source


def test_command_center_can_handoff_unknown_query_to_ai():
    source = Path("command_center.py").read_text(encoding="utf-8")
    assert 'st.session_state["razync_ai_pending_question"] = query' in source
    assert 'navigate("Assistente Razync")' in source
