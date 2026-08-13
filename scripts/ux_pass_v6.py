from pathlib import Path

app = Path('app.py')
ui = Path('ui_system.py')
s = app.read_text(encoding='utf-8')
u = ui.read_text(encoding='utf-8')

# ---------- UI system: empty states + more polished forms ----------
if '.rz-empty {' not in u:
    marker = '/* Native controls */'
    css = '''
/* Product-level surfaces */
[data-testid="stForm"] { background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:16px; padding:1rem 1.05rem .9rem; box-shadow:var(--rz-shadow-soft); }
[data-testid="stForm"] [data-testid="stWidgetLabel"] p { font-size:.82rem; font-weight:650; }
.rz-empty { background:var(--rz-surface); border:1px dashed var(--rz-border); border-radius:15px; padding:24px 20px; text-align:center; margin:.3rem 0 1rem; }
.rz-empty-icon { width:38px; height:38px; border-radius:12px; margin:0 auto 10px; display:flex; align-items:center; justify-content:center; background:var(--rz-primary-soft); color:var(--rz-primary); font-size:1.05rem; font-weight:800; }
.rz-empty-title { color:var(--rz-text); font-size:.96rem; font-weight:760; }
.rz-empty-text { color:var(--rz-muted); font-size:.82rem; line-height:1.45; max-width:560px; margin:5px auto 0; }
.rz-helper { background:var(--rz-soft); border:1px solid var(--rz-border); border-radius:12px; padding:10px 12px; color:var(--rz-muted); font-size:.8rem; margin:.2rem 0 .8rem; }
'''
    u = u.replace(marker, css + '\n' + marker, 1)

if 'def empty_state(' not in u:
    anchor = '\ndef apply_plot_theme('
    helper = '''\n\ndef empty_state(title: str, text: str, icon: str = "○") -> None:\n    st.markdown(\n        f'<div class="rz-empty"><div class="rz-empty-icon">{icon}</div><div class="rz-empty-title">{title}</div><div class="rz-empty-text">{text}</div></div>',\n        unsafe_allow_html=True,\n    )\n\n\ndef helper_note(text: str) -> None:\n    st.markdown(f'<div class="rz-helper">{text}</div>', unsafe_allow_html=True)\n'''
    u = u.replace(anchor, helper + anchor, 1)

s = s.replace(
    'from ui_system import inject_design_system, page_header, section, business_card, alert_card, apply_plot_theme, tokens',
    'from ui_system import inject_design_system, page_header, section, business_card, alert_card, empty_state, helper_note, apply_plot_theme, tokens',
    1,
)

# ---------- Movements: guided form ----------
start = s.index('elif page == "Movimentações":')
end = s.index('\nelif page == "Importar Extrato":', start)
new = '''elif page == "Movimentações":
    header("Movimentações", "Registre o que entrou e saiu do negócio. Os detalhes adicionais são opcionais.")
    section("Novo lançamento", "Comece pelas informações essenciais.")
    with st.form("tx_form", clear_on_submit=True):
        tx_type = st.radio("O que aconteceu?", ["Receita", "Despesa"], horizontal=True)
        a,b = st.columns([1,1])
        value = a.number_input("Valor", min_value=0.0, step=10.0, placeholder="0,00")
        tx_date = b.date_input("Data", date.today())
        desc = st.text_input("Descrição", placeholder="Ex.: pagamento de cliente, compra de material...")
        with st.expander("Mais detalhes (opcional)"):
            a,b = st.columns(2)
            category = a.selectbox("Categoria", ["Serviços","Vendas","Fornecedores","Aluguel","Transporte","Marketing","Impostos","Folha","Outras"])
            counterparty = b.text_input("Cliente ou fornecedor")
            a,b = st.columns(2)
            payment_method = a.selectbox("Forma de pagamento", ["PIX","Dinheiro","Cartão","Boleto","Transferência","Outro"])
            document_number = b.text_input("Nota ou documento")
        if st.form_submit_button("Salvar movimentação", type="primary", use_container_width=True):
            if not desc.strip() or value <= 0:
                st.error("Informe uma descrição e um valor maior que zero.")
            else:
                add_transaction(uid, tx_date=tx_date, tx_type=tx_type, description=desc.strip(), category=category, value=float(value), document_number=document_number.strip(), counterparty=counterparty.strip(), payment_method=payment_method)
                st.rerun()

    section("Histórico", "Seus lançamentos mais recentes e os dados usados nos relatórios.")
    if transactions.empty:
        empty_state("Nenhuma movimentação registrada", "Quando você salvar a primeira receita ou despesa, ela aparecerá aqui e começará a alimentar o financeiro do Razync Pro.", "↕")
    else:
        st.dataframe(transactions[["id","tx_date","tx_type","description","category","counterparty","value"]], use_container_width=True, hide_index=True, column_config={"tx_date":st.column_config.DateColumn("Data", format="DD/MM/YYYY"), "value":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        with st.expander("Gerenciar lançamento"):
            selected = st.selectbox("Lançamento", transactions["id"].tolist())
            st.caption("A exclusão é definitiva e remove o lançamento dos relatórios.")
            if st.button("Excluir lançamento", use_container_width=True):
                delete_transaction(uid, int(selected)); st.rerun()
'''
s = s[:start] + new + s[end:]

# ---------- Invoices ----------
start = s.index('elif page == "Notas Fiscais":')
end = s.index('\nelif page == "DAS":', start)
new = '''elif page == "Notas Fiscais":
    header("Notas Fiscais", "Registre as emissões e acompanhe se cada nota já está refletida no faturamento.")
    section("Registrar nota", "Preencha primeiro os dados principais da emissão.")
    with st.form("invoice_form", clear_on_submit=True):
        a,b = st.columns(2)
        customer = a.text_input("Cliente", placeholder="Nome ou razão social")
        amount = b.number_input("Valor", min_value=0.0, step=10.0)
        a,b,c = st.columns(3)
        issue_date = a.date_input("Data de emissão", date.today())
        invoice_type = b.selectbox("Tipo", ["Serviço","Mercadoria"])
        number = c.text_input("Número da nota")
        with st.expander("Mais detalhes (opcional)"):
            customer_document = st.text_input("CPF/CNPJ do cliente")
            description = st.text_input("Descrição da nota")
            status = st.selectbox("Situação", ["Emitida","Cancelada","Substituída"])
        if st.form_submit_button("Registrar nota", type="primary", use_container_width=True):
            if amount <= 0 or not customer.strip():
                st.error("Informe o cliente e um valor maior que zero.")
            else:
                add_invoice(uid, issue_date=issue_date, invoice_type=invoice_type, number=number.strip(), customer=customer.strip(), customer_document=customer_document.strip(), description=description.strip(), amount=float(amount), status=status)
                st.rerun()
    st.link_button("Abrir Emissor Nacional de NFS-e", "https://www.nfse.gov.br/EmissorNacional", use_container_width=True)
    section("Notas registradas")
    if invoices.empty:
        empty_state("Nenhuma nota registrada", "Registre uma nota emitida para acompanhar faturamento e conciliação com as receitas.", "▧")
    else:
        st.dataframe(invoices[["id","issue_date","invoice_type","number","customer","amount","status"]], use_container_width=True, hide_index=True, column_config={"issue_date":st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"), "amount":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        active = invoices[invoices["status"]=="Emitida"]
        documented = set(transactions["document_number"].fillna("").astype(str)) if not transactions.empty else set()
        unreconciled = active[~active["number"].fillna("").astype(str).isin(documented)]
        if not unreconciled.empty:
            helper_note(f"{len(unreconciled)} nota(s) emitida(s) ainda não estão vinculadas a uma receita pelo número do documento.")
            selected = st.selectbox("Nota para conciliar", unreconciled["id"].tolist())
            row = unreconciled[unreconciled["id"]==selected].iloc[0]
            if st.button("Criar receita e conciliar", type="primary", use_container_width=True):
                add_transaction(uid, tx_date=row["issue_date"].date(), tx_type="Receita", description=row["description"] or f"Nota {row['number']}", category="Serviços" if row["invoice_type"]=="Serviço" else "Vendas", value=float(row["amount"]), document_number=str(row["number"] or ""), counterparty=str(row["customer"] or ""), payment_method="Outro")
                st.rerun()
        with st.expander("Gerenciar notas"):
            iid = st.selectbox("Nota", invoices["id"].tolist())
            if st.button("Excluir nota do controle", use_container_width=True):
                delete_invoice(uid, int(iid)); st.rerun()
'''
s = s[:start] + new + s[end:]

# ---------- Contacts ----------
start = s.index('elif page == "Clientes e Fornecedores":')
end = s.index('\nelif page == "Empregado":', start)
new = '''elif page == "Clientes e Fornecedores":
    header("Clientes e Fornecedores", "Mantenha os contatos usados nas vendas, compras e documentos.")
    section("Novo contato")
    with st.form("contact_form", clear_on_submit=True):
        a,b = st.columns([1,2])
        ctype = a.selectbox("Tipo", ["Cliente","Fornecedor"])
        name = b.text_input("Nome", placeholder="Nome ou razão social")
        with st.expander("Dados de contato (opcional)"):
            a,b,c = st.columns(3)
            document = a.text_input("CPF/CNPJ")
            email = b.text_input("E-mail")
            phone = c.text_input("Telefone")
            notes = st.text_area("Observações", height=90)
        if st.form_submit_button("Salvar contato", type="primary", use_container_width=True):
            if not name.strip(): st.error("Informe o nome do contato.")
            else: add_contact(uid, contact_type=ctype, name=name.strip(), document=document, email=email, phone=phone, notes=notes); st.rerun()
    section("Contatos")
    cdf = pd.DataFrame(list_contacts(uid))
    if cdf.empty:
        empty_state("Nenhum contato cadastrado", "Adicione clientes e fornecedores para deixar lançamentos e documentos mais organizados.", "◇")
    else:
        st.dataframe(cdf, use_container_width=True, hide_index=True)
        with st.expander("Gerenciar contato"):
            cid = st.selectbox("Contato", cdf["id"].tolist())
            if st.button("Excluir contato", use_container_width=True): delete_contact(uid, int(cid)); st.rerun()
'''
s = s[:start] + new + s[end:]

# ---------- Employee ----------
start = s.index('elif page == "Empregado":')
end = s.index('\nelif page == "Documentos":', start)
new = '''elif page == "Empregado":
    header("Empregado", "Organize os dados básicos do empregado do MEI para conferências e declaração anual.")
    section("Cadastrar empregado")
    with st.form("employee_form", clear_on_submit=True):
        name = st.text_input("Nome", placeholder="Nome completo")
        a,b = st.columns(2)
        cpf = a.text_input("CPF")
        admission = b.date_input("Data de admissão", date.today())
        with st.expander("Mais detalhes"):
            a,b = st.columns(2)
            salary = a.number_input("Salário", min_value=0.0)
            status = b.selectbox("Status", ["Ativo","Desligado"])
            notes = st.text_area("Observações", height=90)
        if st.form_submit_button("Salvar empregado", type="primary", use_container_width=True):
            if not name.strip(): st.error("Informe o nome do empregado.")
            else: add_employee(uid, name=name.strip(), cpf=cpf, admission_date=admission, salary=float(salary), status=status, notes=notes); st.rerun()
    section("Empregados")
    edf = pd.DataFrame(list_employees(uid))
    if edf.empty:
        empty_state("Nenhum empregado cadastrado", "Se o MEI possuir empregado, cadastre aqui para manter essa informação disponível nos relatórios anuais.", "♙")
    else:
        st.dataframe(edf, use_container_width=True, hide_index=True)
        with st.expander("Gerenciar empregado"):
            eid = st.selectbox("Empregado", edf["id"].tolist())
            if st.button("Excluir empregado", use_container_width=True): delete_employee(uid, int(eid)); st.rerun()
'''
s = s[:start] + new + s[end:]

# ---------- Documents ----------
start = s.index('elif page == "Documentos":')
end = s.index('\nelif page == "Central de Relatórios":', start)
new = '''elif page == "Documentos":
    header("Documentos", "Guarde notas, recibos, comprovantes, DAS, extratos e outros arquivos importantes do MEI.")
    section("Adicionar documento")
    with st.form("doc_form", clear_on_submit=True):
        uploaded = st.file_uploader("Arquivo", type=["pdf","png","jpg","jpeg","xlsx","csv"])
        a,b = st.columns(2)
        category = a.selectbox("Categoria", ["Nota fiscal","Recibo","Comprovante","DAS","DASN-SIMEI","Contrato","Extrato","Outro"])
        reference_month = b.text_input("Competência", placeholder="AAAA-MM")
        st.caption("A competência ajuda o fechamento mensal a localizar o documento certo.")
        if st.form_submit_button("Salvar documento", type="primary", use_container_width=True):
            if uploaded is None: st.error("Selecione um arquivo.")
            else: save_document(uid, uploaded.name, uploaded.type or "", uploaded.getvalue(), category, reference_month.strip()); st.rerun()

    ddf = pd.DataFrame(list_documents(uid))
    section("Arquivos armazenados")
    if ddf.empty:
        empty_state("Seu cofre ainda está vazio", "Adicione o primeiro documento para começar a organizar comprovantes e competências em um só lugar.", "▤")
    else:
        coverage_year = st.selectbox("Ano da cobertura", list(range(CURRENT_YEAR-3, CURRENT_YEAR+2))[::-1], key="docs_coverage_year")
        coverage = document_coverage(docs, int(coverage_year))
        c1,c2 = st.columns(2)
        c1.metric("Documentos", len(docs))
        c2.metric("Meses com arquivos", int((coverage["Documentos"] > 0).sum()))
        with st.expander("Ver cobertura por competência"):
            st.dataframe(coverage, use_container_width=True, hide_index=True)
        st.dataframe(ddf, use_container_width=True, hide_index=True)
        with st.expander("Gerenciar documento"):
            did = st.selectbox("Documento", ddf["id"].tolist())
            doc = get_document(uid, int(did))
            if doc:
                a,b = st.columns(2)
                a.download_button("Baixar documento", doc["content"], doc["filename"], doc.get("mime_type") or "application/octet-stream", use_container_width=True)
                if b.button("Excluir documento", use_container_width=True): delete_document(uid, int(did)); st.rerun()
'''
s = s[:start] + new + s[end:]

# ---------- Custom obligations empty state ----------
s = s.replace('if odf.empty: st.info("Nenhuma obrigação cadastrada.")', 'if odf.empty: empty_state("Nenhuma tarefa personalizada", "O calendário automático continua funcionando. Crie uma tarefa aqui apenas quando precisar acompanhar algo específico do seu MEI.", "✓")')

# ---------- DAS empty year state ----------
needle = '''        if not ddf.empty:\n            ddf["status_atual"] = [das_status(r["status"],r["due_date"]) for _,r in ddf.iterrows()]\n            st.dataframe(ddf[["competence","due_date","amount","status_atual","payment_date","notes"]],use_container_width=True,hide_index=True,column_config={"due_date":st.column_config.DateColumn("Vencimento",format="DD/MM/YYYY"),"amount":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"payment_date":st.column_config.DateColumn("Pagamento",format="DD/MM/YYYY")})'''
replace = needle + '''\n        else:\n            empty_state("Calendário ainda não criado", "Gere o calendário anual para acompanhar vencimentos e pagamentos do DAS por competência.", "▣")'''
if needle in s and 'Calendário ainda não criado' not in s:
    s = s.replace(needle, replace, 1)

# ---------- Generic empty analysis ----------
s = s.replace('st.info("Ainda não existem despesas no período.")', 'empty_state("Sem despesas no período", "Quando houver despesas registradas, a distribuição por categoria aparecerá aqui.", "◫")')

app.write_text(s, encoding='utf-8')
ui.write_text(u, encoding='utf-8')
print('UX pass v6 applied')
