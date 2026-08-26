from pathlib import Path

from brand_assets import brand_logo_data_uri, ensure_brand_assets


def test_official_logo_is_available_for_streamlit_and_browser():
    logo_path = Path(ensure_brand_assets())

    assert logo_path.exists()
    assert logo_path.suffix == ".jpg"
    assert logo_path.read_bytes().startswith(b"\xff\xd8\xff")
    assert brand_logo_data_uri().startswith("data:image/jpeg;base64,")


def test_app_uses_official_logo_for_favicon_login_and_sidebar():
    app_source = Path("app.py").read_text(encoding="utf-8")
    sidebar_source = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    demo_source = Path("demo_mode.py").read_text(encoding="utf-8")

    assert "page_icon=BRAND_LOGO_PATH" in app_source
    assert 'alt="Logo Razync Pro"' in app_source
    assert 'alt="Razync Pro"' in sidebar_source
    assert "brand_logo_data_uri" in demo_source
    assert "rz-brand-mark" in demo_source

