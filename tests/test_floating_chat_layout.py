from pathlib import Path


def test_floating_chat_no_longer_uses_popover():
    sidebar = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    floating = Path("floating_assistant.py").read_text(encoding="utf-8")

    assert "st.popover" not in sidebar
    assert 'key="floating_ai_panel"' in sidebar
    assert 'key="floating_ai_launcher"' in sidebar
    assert 'key="floating_ai_thread"' in floating
    assert 'key="floating_ai_composer"' in floating
    assert 'st.form("floating_ai_form"' in floating
