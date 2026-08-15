from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "demo_mode.py").read_text(encoding="utf-8")


def test_demo_has_visible_sidebar_navigation():
    assert "with st.sidebar:" in SOURCE
    assert 'st.session_state.get("_demo_section", "Visão geral")' in SOURCE
    assert 'st.session_state["_demo_section"] = destination' in SOURCE
    assert "Visão geral" in SOURCE
    assert "Financeiro" in SOURCE
    assert "Automações" in SOURCE
    assert "Fiscal e DAS" in SOURCE


def test_design_system_does_not_hide_demo_sidebar():
    design_source = (Path(__file__).resolve().parents[1] / "ui_system.py").read_text(encoding="utf-8")
    assert '.stApp:has(.rz-demo-shell) [data-testid="stSidebar"]' not in design_source
    assert '[data-testid="stExpandSidebarButton"]' in design_source
    assert "position:fixed!important" in design_source
    assert '[data-testid="stToolbar"] {{ display:flex!important' in design_source


def test_demo_can_return_to_the_real_system():
    assert "Entrar no sistema" in SOURCE
    assert "_leave_demo" in SOURCE
    assert 'st.session_state.pop("_demo_mode", None)' in SOURCE
