from pathlib import Path
from unittest.mock import patch
from ui_system import inject_design_system, tokens


def test_design_system_emits_theme_tokens():
    with patch('ui_system.st.markdown') as markdown:
        inject_design_system('Claro')
    css = markdown.call_args.args[0]
    assert '--rz-primary:#087f79' in css
    assert '--rz-text:#172c35' in css
    assert 'stExpandSidebarButton' in css


def test_form_controls_have_focus_and_theme_support():
    css = Path('workspace.css').read_text(encoding='utf-8')
    assert ':focus-within' in css
    assert ':focus-visible' in css
    assert 'var(--rz-surface)' in css
    assert '[data-baseweb="input"]' in css
    assert '[data-baseweb="select"]' in css


def test_new_transaction_preserves_semantic_choices():
    source = Path('app.py').read_text(encoding='utf-8')
    assert 'key="tx_type_new"' in source
    assert 'Entrada' in source
    assert 'Saída' in source


def test_light_and_dark_palettes_are_distinct():
    light, dark = tokens('Claro'), tokens('Escuro')
    assert light['primary'] == '#087f79'
    assert dark['primary'] == '#5ad6c4'
    assert light['surface'] != dark['surface']
    assert light['text'] != dark['text']
    assert light['plot'] == 'plotly_white'
    assert dark['plot'] == 'plotly_dark'


def test_workspace_has_responsive_shared_components():
    css = Path('workspace.css').read_text(encoding='utf-8')
    assert 'st-key-workspace_metrics' in css
    assert 'st-key-overview_welcome' in css
    assert 'prefers-reduced-motion' in css
    assert 'grid-template-columns: repeat(2,minmax(0,1fr))' in css
