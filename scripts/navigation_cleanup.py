from pathlib import Path
import re

# Streamlit 1.61+: replace deprecated width argument everywhere in Python sources.
for path in Path('.').rglob('*.py'):
    if any(part in {'.git', '.venv', 'venv'} for part in path.parts):
        continue
    text = path.read_text(encoding='utf-8')
    updated = text.replace('use_container_width=True', 'width="stretch"')
    updated = updated.replace('use_container_width=False', 'width="content"')
    if updated != text:
        path.write_text(updated, encoding='utf-8')

# Simplify visible navigation: remove intermediary hubs and surface the assistant.
pc = Path('product_core.py')
text = pc.read_text(encoding='utf-8')
old = '''NAV_GROUPS = {\n    "Visão Geral": ["Dashboard"],\n    "Financeiro": ["Movimentações", "Recorrências", "Importar Extrato", "Conciliação", "Fluxo de Caixa", "Análise Financeira"],\n    "Fiscal MEI": ["Central Fiscal", "Fechamento Mensal", "Relatório Mensal", "Notas Fiscais", "DAS", "DASN-SIMEI", "Obrigações"],\n    "Gestão": ["Clientes e Fornecedores", "Empregado", "Documentos"],\n    "Relatórios": ["Central de Relatórios", "Assistente Razync"],\n    "Configurações": ["Primeiros Passos", "Meu MEI", "Segurança da Conta", "Status do Sistema", "Backup"],\n}\n'''
new = '''NAV_GROUPS = {\n    "Visão Geral": ["Dashboard", "Assistente Razync"],\n    "Financeiro": ["Movimentações", "Recorrências", "Importar Extrato", "Conciliação", "Fluxo de Caixa", "Análise Financeira"],\n    "Fiscal MEI": ["DAS", "DASN-SIMEI", "Obrigações", "Notas Fiscais", "Relatório Mensal", "Fechamento Mensal"],\n    "Gestão": ["Clientes e Fornecedores", "Empregado", "Documentos"],\n    "Configurações": ["Primeiros Passos", "Meu MEI", "Segurança da Conta", "Status do Sistema", "Backup"],\n}\n'''
if old not in text:
    raise SystemExit('NAV_GROUPS block not found')
text = text.replace(old, new, 1)
text = text.replace('"page": "Central Fiscal"', '"page": "Análise Financeira"')
pc.write_text(text, encoding='utf-8')

# Remove the two intermediary-only page blocks and point the dashboard fiscal shortcut directly to DAS.
app = Path('app.py')
a = app.read_text(encoding='utf-8')
a = a.replace('st.session_state["_navigate_to"] = "Central Fiscal"', 'st.session_state["_navigate_to"] = "DAS"')
a = a.replace('st.session_state["_navigate_to"]="Central Fiscal"', 'st.session_state["_navigate_to"]="DAS"')

def remove_block(source: str, start: str, end: str) -> str:
    start_idx = source.find(start)
    if start_idx < 0:
        return source
    end_idx = source.find(end, start_idx)
    if end_idx < 0:
        raise SystemExit(f'end marker not found for {start}')
    return source[:start_idx] + source[end_idx:]

a = remove_block(a, 'elif page == "Central Fiscal":', 'elif page == "Fechamento Mensal":')
a = remove_block(a, 'elif page == "Central de Relatórios":', 'elif page == "Assistente Razync":')
app.write_text(a, encoding='utf-8')

# Ensure no deprecated Streamlit width argument remains in production Python files.
remaining = []
for path in Path('.').rglob('*.py'):
    if 'use_container_width=' in path.read_text(encoding='utf-8'):
        remaining.append(str(path))
if remaining:
    raise SystemExit('deprecated use_container_width remains in: ' + ', '.join(remaining))

print('Navigation cleanup and Streamlit width migration applied.')
