from __future__ import annotations

from pathlib import Path


def test_sidebar_redirects_legacy_assistant_page_to_floating_chat():
    source = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    assert 'if page == "Assistente Razync"' in source
    assert 'st.session_state[_FLOATING_OPEN_KEY] = True' in source
    assert 'navigate("Dashboard")' in source


def test_floating_host_navigation_cannot_open_dedicated_assistant_page():
    source = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    assert 'if destination == "Assistente Razync"' in source
    assert 'render_isolated_chat_v7(user=user, page=page, navigate=floating_navigate)' in source


def test_contextual_dashboard_and_productivity_ai_buttons_open_floating_chat():
    contextual = Path("contextual_ai.py").read_text(encoding="utf-8")
    dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
    productivity = Path("productivity_workspace.py").read_text(encoding="utf-8")

    assert 'razync_floating_open' in contextual
    assert 'navigate("Assistente Razync")' not in contextual
    assert 'st.session_state["razync_floating_open"] = True' in dashboard
    assert 'navigate("Assistente Razync")' not in dashboard
    assert '"Razync IA"' in productivity
    assert 'razync_floating_open' in productivity
    assert '("Assistente Razync"' not in productivity


def test_command_center_uses_floating_action_instead_of_assistant_route():
    source = Path("command_center.py").read_text(encoding="utf-8")
    assert '_FLOATING_AI_COMMAND = "__floating_ai__"' in source
    assert '(_FLOATING_AI_COMMAND, "Perguntar à IA")' in source
    assert '("Assistente Razync", "Perguntar à IA"' not in source
    assert 'st.session_state["razync_floating_open"] = True' in source


def test_navigation_does_not_expose_dedicated_assistant_destination():
    source = Path("navigation_config.py").read_text(encoding="utf-8")
    assert '"Assistente Razync": "Assistente"' not in source
    assert '"Assistente Razync": ":material/auto_awesome:"' not in source


def test_pending_queries_are_consumed_by_floating_bridge():
    source = Path("floating_ai_bridge.py").read_text(encoding="utf-8")
    assert 'st.session_state.pop(_PENDING_QUESTION_KEY' in source
    assert '_process_question(question, snapshot=snapshot, page=page)' in source
