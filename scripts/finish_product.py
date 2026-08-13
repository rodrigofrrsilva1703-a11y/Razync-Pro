from pathlib import Path

app = Path("app.py")
s = app.read_text(encoding="utf-8")

if "from database import database_runtime_info" not in s:
    s = s.replace("from fiscal_rules import (", "from database import database_runtime_info\nfrom fiscal_rules import (", 1)
if "from backup_tools import" not in s:
    s = s.replace("from product_core import NAV_GROUPS, group_for_page, action_items, reconciliation_summary, assistant_answer\n", "from product_core import NAV_GROUPS, group_for_page, action_items, reconciliation_summary, assistant_answer\nfrom backup_tools import build_backup_zip, document_coverage\n", 1)

old_docs = '''elif page == "Documentos":\n    header("Documentos","Cofre de notas, recibos, comprovantes, DAS e outros documentos do MEI.")\n    with st.form("doc_form",clear_on_submit=True):\n'''
new_docs = '''elif page == "Documentos":\n    header("Documentos","Cofre de notas, recibos, comprovantes, DAS e outros documentos do MEI.")\n    coverage_year = st.selectbox("Ano da cobertura documental", list(range(CURRENT_YEAR-3, CURRENT_YEAR+2))[::-1], key="docs_coverage_year")\n    coverage = document_coverage(docs, int(coverage_year))\n    c1,c2 = st.columns(2)\n    c1.metric("Documentos armazenados", len(docs))\n    c2.metric("Meses com documentos", int((coverage["Documentos"] > 0).sum()))\n    st.dataframe(coverage, use_container_width=True, hide_index=True)\n    st.caption("Use o mês de referência no formato AAAA-MM para que o fechamento mensal consiga localizar os documentos da competência.")\n    with st.form("doc_form",clear_on_submit=True):\n'''
if old_docs in s and "Ano da cobertura documental" not in s:
    s = s.replace(old_docs, new_docs, 1)

backup_start = s.find('elif page == "Backup":')
footer_start = s.find('\nst.divider()\nst.caption("Razync Pro', backup_start)
if backup_start != -1 and footer_start != -1:
    backup_block = '''elif page == "Backup":\n    header("Backup e exportação","Baixe uma cópia consolidada ou arquivos separados dos dados cadastrados.")\n    backup_zip = build_backup_zip(profile, transactions, invoices, das_rows, contacts, obligations, employees, docs)\n    st.download_button("Baixar backup completo (.zip)", backup_zip, f"razync_pro_backup_{date.today().isoformat()}.zip", "application/zip", type="primary", use_container_width=True)\n    st.caption("O ZIP contém perfil, movimentações, notas fiscais, DAS, contatos, obrigações, empregados e índice de documentos.")\n    st.subheader("Arquivos individuais")\n    files={"movimentacoes.csv":transactions.to_csv(index=False).encode("utf-8-sig"),"notas_fiscais.csv":invoices.to_csv(index=False).encode("utf-8-sig"),"das.csv":pd.DataFrame(das_rows).to_csv(index=False).encode("utf-8-sig"),"contatos.csv":pd.DataFrame(contacts).to_csv(index=False).encode("utf-8-sig"),"obrigacoes.csv":pd.DataFrame(obligations).to_csv(index=False).encode("utf-8-sig")}\n    for name,data in files.items(): st.download_button(f"Baixar {name}",data,name,"text/csv",use_container_width=True)\n\n'''
    s = s[:backup_start] + backup_block + s[footer_start:]

status_marker = 'elif page == "Backup":\n'
if status_marker in s and 'elif page == "Status do Sistema"' not in s:
    status_page = '''elif page == "Status do Sistema":\n    header("Status do Sistema","Veja o que já está operacional e o que ainda depende de configuração externa.")\n    dbinfo = database_runtime_info()\n    c1,c2,c3 = st.columns(3)\n    c1.metric("Banco de dados", dbinfo["backend"])\n    c2.metric("Persistência", "Ativa" if dbinfo["persistent"] else "Temporária")\n    c3.metric("Banco de produção", "Pronto" if dbinfo["production_ready"] else "Pendente")\n    if dbinfo["persistent"]:\n        st.success("O Razync Pro está conectado a PostgreSQL e os dados podem ser mantidos fora do ciclo temporário do Streamlit.")\n    else:\n        st.warning("O sistema está usando SQLite temporário. Para dados reais, configure DATABASE_URL nos Secrets do Streamlit apontando para PostgreSQL/Supabase.")\n    st.subheader("Integrações")\n    integration_rows = pd.DataFrame([\n        {"Integração":"Importação de extrato CSV/Excel", "Status":"Operacional", "Observação":"Importação com prévia, categorização sugerida e controle de duplicidade."},\n        {"Integração":"PostgreSQL / Supabase", "Status":"Operacional" if dbinfo["persistent"] else "Aguardando credencial", "Observação":"Suporte no código concluído; requer DATABASE_URL do banco gerenciado."},\n        {"Integração":"NFS-e Nacional", "Status":"Controle manual", "Observação":"Notas podem ser controladas e conciliadas; integração automática depende do fluxo/API oficial aplicável ao emissor."},\n        {"Integração":"Assistente Razync", "Status":"Operacional", "Observação":"Consulta faturamento, despesas, limite, DAS e conciliação com base nos dados cadastrados."},\n    ])\n    st.dataframe(integration_rows, use_container_width=True, hide_index=True)\n\n'''+status_marker
    s = s.replace(status_marker, status_page, 1)

app.write_text(s, encoding="utf-8")

core = Path("product_core.py")
c = core.read_text(encoding="utf-8")
c = c.replace('"Configurações": ["Meu MEI", "Backup"],', '"Configurações": ["Meu MEI", "Status do Sistema", "Backup"],')
core.write_text(c, encoding="utf-8")
print("final product layer applied")
