from pathlib import Path

from floating_chat_v7_host import (
    _MAX_COMPONENT_DOWNLOAD_BYTES,
    _component_resources,
)


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
    assert '"open_resource_route"' in html
    assert 'className="action-card"' in html
    assert 'className="receipt-card"' in html
    assert 'className="quick-actions"' in html
    assert "renderMarkdown" in html
    assert "escapeHtml" in html
    assert "maxDocumentBytes" in html
    assert "maxAudioBytes" in html
    assert "file.size>maxBytes" in html
    assert "confirm_automation" in host
    assert "revise_automation" in host
    assert "_pending_action_card" in host
    assert "_component_resources" in host
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


def test_v7_resources_are_serialized_for_safe_downloads():
    bundle = {
        "downloads": [
            {
                "label": "Baixar relatório",
                "data": b"pdf-bytes",
                "file_name": "relatorio.pdf",
                "mime": "application/pdf",
            }
        ],
        "route": "Documentos",
        "route_label": "Abrir Documentos",
        "note": "Arquivo pronto.",
    }
    result = _component_resources(bundle)
    assert result["route"] == "Documentos"
    assert result["downloads"][0]["file_name"] == "relatorio.pdf"
    assert result["downloads"][0]["href"].startswith("data:application/pdf;base64,")
    assert result["note"] == "Arquivo pronto."


def test_v7_large_resource_is_not_embedded_in_component_payload():
    bundle = {
        "downloads": [
            {
                "label": "Arquivo grande",
                "data": b"x" * (_MAX_COMPONENT_DOWNLOAD_BYTES + 1),
                "file_name": "grande.pdf",
                "mime": "application/pdf",
            }
        ],
        "route": "Documentos",
        "route_label": "Abrir Documentos",
    }
    result = _component_resources(bundle)
    assert result["downloads"] == []
    assert "grandes demais" in str(result["note"])
    assert result["route"] == "Documentos"


def test_v7_event_deduplication_is_kept():
    host = Path("floating_chat_v7_host.py").read_text(encoding="utf-8")
    assert '_LAST_EVENT_KEY = "razync_chat_v7_last_event"' in host
    assert "event_id == str(st.session_state.get(_LAST_EVENT_KEY)" in host
