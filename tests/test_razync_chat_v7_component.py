from pathlib import Path


def test_v7_chat_is_isolated_from_streamlit_widgets():
    html = Path("components/razync_chat/index.html").read_text(encoding="utf-8")
    host = Path("floating_chat_v7_host.py").read_text(encoding="utf-8")

    assert 'streamlit:setComponentValue' in html
    assert 'streamlit:componentReady' in html
    assert 'streamlit:render' in html
    assert 'class="thread"' in html
    assert 'class="composer"' in html
    assert 'id="send"' in html
    assert 'function dispatchPrompt(text,action="send")' in html
    assert 'dispatchPrompt(String(item.prompt),"quick_prompt")' in html
    assert '"confirm_action"' in html
    assert '"cancel_action"' in html
    assert '"update_action"' in html
    assert '"upload_document"' in html
    assert '"upload_audio"' in html
    assert '"open_receipt"' in html
    assert '"undo_action"' in html
    assert 'className="action-card"' in html
    assert 'className="receipt-card"' in html
    assert 'className="quick-actions"' in html
    assert "confirm_automation" in host
    assert "revise_automation" in host
    assert "_pending_action_card" in host
    assert 'st.popover' not in host
    assert 'st.chat_message' not in host
    assert 'st.form' not in host


def test_v7_is_connected_to_sidebar_without_popover():
    sidebar = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    assert "render_isolated_chat_v7" in sidebar
    assert "floating_chat_v7_host" in sidebar
    assert 'key="floating_ai_v7_shell"' in sidebar
    assert 'key="floating_ai_launcher"' in sidebar
    assert "st.popover" not in sidebar

