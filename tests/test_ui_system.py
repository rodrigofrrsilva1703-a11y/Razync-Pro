from unittest.mock import patch

from ui_system import inject_design_system, tokens


def test_login_design_system_renders_without_template_errors():
    with patch("ui_system.st.markdown") as markdown:
        inject_design_system("Claro")

    css = markdown.call_args.args[0]
    assert ".rz-login-shell" in css
    assert ":has(.rz-login-shell)" in css
    assert "display:none" in css
    assert ".rz-auth-heading" in css
    assert ".rz-login-security" in css
    assert "backdrop-filter:blur(18px)" in css
    assert '[data-baseweb="input"]' in css
    assert "button p { color:white!important; }" in css
    assert '[data-testid="stLinkButton"]' in css
    assert "prefers-reduced-motion" in css
    assert ".rz-demo-shell" in css
    assert ".rz-mobile-card" in css
    assert ".rz-status-grid" in css


def test_brand_palette_preserves_distinct_light_and_dark_modes():
    light = tokens("Claro")
    dark = tokens("Escuro")

    assert light["primary"] == "#08b9ef"
    assert dark["primary"] == "#10bdf2"
    assert light["bg"] == "#f1f6fa"
    assert dark["bg"] == "#07111b"
    assert light["surface"] != dark["surface"]
    assert light["text"] != dark["text"]
    assert light["plot"] == "plotly_white"
    assert dark["plot"] == "plotly_dark"
