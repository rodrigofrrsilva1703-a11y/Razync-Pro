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
    assert 'action:"send"' in html
    assert 'st.popover' not in host
    assert 'st.chat_message' not in host
    assert 'st.form' not in host


def test_v7_is_not_connected_to_production_sidebar_yet():
    sidebar = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    assert "render_isolated_chat_v7" not in sidebar
    assert "floating_chat_v7_host" not in sidebar
