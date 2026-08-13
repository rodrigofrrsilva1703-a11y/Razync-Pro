from pathlib import Path

app = Path('app.py')
db = Path('database.py')
core = Path('product_core.py')

s = app.read_text(encoding='utf-8')
d = db.read_text(encoding='utf-8')
c = core.read_text(encoding='utf-8')

anchor = '''def delete_transaction(user_id: int, item_id: int) -> None:\n    with engine.begin() as conn:\n        conn.execute(delete(transactions).where(transactions.c.user_id == user_id, transactions.c.id == item_id))\n'''
helper = anchor + '''\n\ndef link_transaction_document(user_id: int, item_id: int, document_number: str, counterparty: str = "") -> None:\n    payload = {"document_number": (document_number or "").strip()}\n    if counterparty:\n        payload["counterparty"] = counterparty.strip()\n    with engine.begin() as conn:\n        conn.execute(update(transactions).where(transactions.c.user_id == user_id, transactions.c.id == item_id).values(**payload))\n'''
if 'def link_transaction_document(' not in d:
    d = d.replace(anchor, helper, 1)

c = c.replace('"Configurações": ["Meu MEI", "Status do Sistema", "Backup"],', '"Configurações": ["Primeiros Passos", "Meu MEI", "Status do Sistema", "Backup"],', 1)

s = s.replace('update_obligation_status, upsert_das,', 'update_obligation_status, upsert_das, link_transaction_document,', 1)
s = s.replace('from backup_tools import build_backup_zip, document_coverage', 'from backup_tools import build_backup_zip, document_coverage\nfrom onboarding_tools import onboarding_progress, recommended_setup\nfrom reconciliation_tools import smart_invoice_matches, duplicate_groups', 1)

needle = '    business_card(business_label, CURRENT_YEAR, cnpj_label)\n\n    today = date.today()'
replacement = '''    business_card(business_label, CURRENT_YEAR, cnpj_label)\n    onboarding = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))\n    if not onboarding["complete"]:\n        st.info(f"Configuração inicial: {onboarding['done']} de {onboarding['total']} etapas concluídas ({onboarding['percent']}%).")\n        if st.button("Continuar configuração do MEI", key="dash_onboarding", use_container_width=True):\n            st.session_state["_navigate_to"] = "Primeiros Passos"\n            st.rerun()\n\n    today = date.today()'''
if needle in s:
    s = s.replace(needle, replacement, 1)

start = s.index('elif page == "Conciliação":')
end = s.index('\nelif page == "Fluxo de Caixa":', start)
new_reconciliation = '''elif page == "Conciliação":
    header("Conciliação Inteligente", "O Razync compara notas e receitas usando número do documento, valor, data e cliente para sugerir correspondências.")
    rec = reconciliation_summary(transactions, invoices)
    matches = smart_invoice_matches(transactions, invoices)
    duplicates = duplicate_groups(transactions)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Notas emitidas", rec["total_invoices"])
    c2.metric("Já conciliadas", rec["reconciled_invoices"])
    c3.metric("Sugestões encontradas", len(matches))
    c4.metric("Possíveis duplicidades", len(duplicates))

    section("Sugestões automáticas", "Revise antes de confirmar. O Razync nunca vincula automaticamente sem sua decisão.")
    if matches.empty:
        empty_state("Nenhuma correspondência forte encontrada", "Você pode importar um extrato ou registrar receitas para o Razync encontrar possíveis vínculos com as notas.", "≈")
    else:
        show_matches = matches.rename(columns={"invoice_number":"Nota","customer":"Cliente","invoice_value":"Valor da nota","tx_date":"Data do lançamento","tx_description":"Lançamento","tx_value":"Valor lançado","score":"Pontuação","confidence":"Confiança","reasons":"Motivos"})
        st.dataframe(show_matches[["Nota","Cliente","Valor da nota","Data do lançamento","Lançamento","Valor lançado","Confiança","Pontuação","Motivos"]], use_container_width=True, hide_index=True, column_config={"Valor da nota":st.column_config.NumberColumn("Valor da nota", format="R$ %.2f"), "Valor lançado":st.column_config.NumberColumn("Valor lançado", format="R$ %.2f"), "Data do lançamento":st.column_config.DateColumn("Data do lançamento", format="DD/MM/YYYY"), "Pontuação":st.column_config.ProgressColumn("Pontuação", min_value=0, max_value=100)})
        option_labels = {int(r.tx_id): f"Nota {r.invoice_number or r.invoice_id} → {r.tx_description} • R$ {r.tx_value:,.2f} • confiança {r.confidence}" for r in matches.itertuples()}
        selected_tx = st.selectbox("Sugestão para revisar", list(option_labels.keys()), format_func=lambda x: option_labels[x], key="smart_match")
        selected = matches[matches["tx_id"] == selected_tx].iloc[0]
        st.caption(f"Motivos: {selected['reasons']} • pontuação {int(selected['score'])}/100")
        if st.button("Confirmar vínculo com este lançamento", type="primary", use_container_width=True):
            link_transaction_document(uid, int(selected["tx_id"]), str(selected["invoice_number"] or ""), str(selected["customer"] or ""))
            st.success("Nota vinculada ao lançamento existente sem criar receita duplicada.")
            st.rerun()

    section("Notas ainda sem vínculo")
    pending_inv = rec["pending_invoices"]
    if pending_inv.empty:
        st.success("Todas as notas numeradas estão conciliadas com receitas cadastradas.")
    else:
        st.dataframe(pending_inv, use_container_width=True, hide_index=True, column_config={"Valor":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        with st.expander("Criar receita a partir de uma nota sem correspondência"):
            selected_invoice = st.selectbox("Nota", pending_inv["ID"].tolist(), key="rec_invoice")
            source = invoices[invoices["id"] == selected_invoice].iloc[0]
            st.caption("Use somente quando não existir um recebimento correspondente entre as movimentações.")
            if st.button("Criar nova receita desta nota", use_container_width=True):
                issue = source["issue_date"]
                tx_date_value = issue.date() if hasattr(issue, "date") else issue
                add_transaction(uid, tx_date=tx_date_value, tx_type="Receita", description=source.get("description") or f"Nota {source.get('number') or ''}", category="Serviços" if source.get("invoice_type") == "Serviço" else "Vendas", value=float(source.get("amount") or 0), document_number=str(source.get("number") or ""), counterparty=str(source.get("customer") or ""), payment_method="Outro")
                st.rerun()

    section("Possíveis lançamentos duplicados")
    if duplicates.empty:
        st.success("Nenhuma duplicidade evidente foi encontrada nas movimentações.")
    else:
        st.dataframe(duplicates, use_container_width=True, hide_index=True, column_config={"tx_date":st.column_config.DateColumn("Data", format="DD/MM/YYYY"), "value":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        with st.expander("Remover duplicidade"):
            duplicate_id = st.selectbox("Lançamento a excluir", duplicates["id"].tolist(), key="duplicate_delete")
            st.caption("Confira os registros antes de excluir. A exclusão é definitiva.")
            if st.button("Excluir lançamento selecionado", use_container_width=True):
                delete_transaction(uid, int(duplicate_id)); st.rerun()

    if st.button("Importar novo extrato", use_container_width=True):
        st.session_state["_navigate_to"] = "Importar Extrato"
        st.rerun()
'''
s = s[:start] + new_reconciliation + s[end:]

anchor = 'elif page == "Meu MEI":'
onboarding_page = '''elif page == "Primeiros Passos":
    header("Primeiros Passos", "Configure o Razync Pro para o seu MEI e deixe os alertas, limites e relatórios mais úteis.")
    progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))
    c1,c2 = st.columns([1,3])
    c1.metric("Configuração", f"{progress['percent']}%")
    with c2:
        st.caption(f"{progress['done']} de {progress['total']} etapas concluídas")
        st.progress(progress["percent"] / 100)

    section("1. Dados essenciais do negócio", "Você pode completar os detalhes avançados depois em Meu MEI.")
    with st.form("onboarding_profile"):
        a,b = st.columns(2)
        business_name = a.text_input("Nome do negócio", value=str(profile.get("trade_name") or profile.get("business_name") or ""))
        cnpj = b.text_input("CNPJ", value=str(profile.get("cnpj") or ""))
        a,b = st.columns(2)
        main_activity = a.text_input("Atividade principal", value=str(profile.get("main_activity") or ""), placeholder="Ex.: design gráfico, comércio de roupas...")
        activity_options = ["Serviços","Comércio","Indústria","Misto"]
        current_activity = profile.get("activity_type") if profile.get("activity_type") in activity_options else "Serviços"
        activity_type = b.selectbox("Tipo de atividade", activity_options, index=activity_options.index(current_activity))
        opening_date = st.date_input("Data de abertura", value=opening or date.today())
        if st.form_submit_button("Salvar configuração básica", type="primary", use_container_width=True):
            save_profile(uid, business_name=business_name, trade_name=business_name, cnpj=cnpj, main_activity=main_activity, activity_type=activity_type, opening_date=opening_date)
            st.rerun()

    section("2. Próximas etapas")
    progress = onboarding_progress(get_profile(uid), not transactions.empty, bool(das_rows), bool(docs))
    for step in progress["steps"]:
        status = "✓" if step["done"] else "○"
        st.write(f"{status} **{step['title']}** — {step['detail']}")

    a,b,c = st.columns(3)
    if a.button("Registrar movimentação", use_container_width=True): st.session_state["_navigate_to"]="Movimentações"; st.rerun()
    if b.button("Configurar DAS", use_container_width=True): st.session_state["_navigate_to"]="DAS"; st.rerun()
    if c.button("Adicionar documento", use_container_width=True): st.session_state["_navigate_to"]="Documentos"; st.rerun()

    section("Recomendações do Razync")
    for tip in recommended_setup(get_profile(uid)):
        helper_note(tip)

'''
if anchor in s and 'elif page == "Primeiros Passos":' not in s:
    s = s.replace(anchor, onboarding_page + anchor, 1)

app.write_text(s, encoding='utf-8')
db.write_text(d, encoding='utf-8')
core.write_text(c, encoding='utf-8')
print('next stage v7 applied')
# trigger v7
