from unittest.mock import patch

from ui_system import inject_design_system


def test_login_design_system_renders_without_template_errors():
    with patch("ui_system.st.markdown") as markdown:
        inject_design_system("Claro")

    css = markdown.call_args.args[0]
    assert ".rz-login-shell" in css
    assert ":has(.rz-login-shell)" in css
    assert "display:none" in css
