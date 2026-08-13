from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Imports
anchor = 'from reports import dasn_summary_pdf, monthly_report_pdf\n'
extra = anchor + 'from bank_import import read_statement, prepare_statement, is_probable_duplicate, suggest_category\nfrom mei_obligations import automatic_obligations\n'
if 'from bank_import import' not in s:
    s = s.replace(anchor, extra, 1)

# Sidebar: adiciona importação de extrato e chave de navegação para ações rápidas.
old_nav = 'page = st.radio("Navegação", ["Dashboard","Movimentações","Fluxo de Caixa","Relatório Mensal","Notas Fiscais","DAS","DASN-SIMEI","Obrigações","Clientes e Fornecedores","Empregado","Documentos","Assistente Razync","Meu MEI","Backup"], label_visibility="collapsed")'
new_nav = 'page = st.radio("Navegação", ["Dashboard","Movimentações","Importar Extrato","Fluxo de Caixa","Relatório Mensal","Notas Fiscais","DAS","DASN-SIMEI","Obrigações","Clientes e Fornecedores","Empregado","Documentos","Assistente Razync","Meu MEI","Backup"], label_visibility="collapsed", key="nav_page")'
if old_nav in s:
    s = s.replace(old_nav, new_nav, 1)

# Remove botão sair do modo dev, pois o acesso é direto.
old_logout = '''    st.divider()\n    st.caption(user["email"])\n    if st.button("Sair", use_container_width=True):\n        st.session_state.pop("user",None)\n        st.rerun()\n'''
new_logout = '''    st.divider()\n    st.caption("Modo de desenvolvimento • acesso direto")\n'''
if old_logout in s:
    s = s.replace(old_logout, new_logout, 1)

# Ações rápidas no Dashboard
marker = '''    c1,c2,c3,c4,c5 = st.columns(5)\n    c1.metric("Receita no ano",brl(year_revenue)); c2.metric("Despesas no ano",brl(year_expense)); c3.metric("Resultado estimado",brl(year_revenue-year_expense)); c4.metric("Limite utilizado",f"{limit_pct:.1f}%"); c5.metric("Documentos",len(docs))\n'''
quick = marker + '''    st.caption("Ações rápidas")\n    q1,q2,q3,q4 = st.columns(4)\n    if q1.button("+ Lançamento", use_container_width=True): st.session_state.nav_page="Movimentações"; st.rerun()\n    if q2.button("Importar extrato", use_container_width=True): st.session_state.nav_page="Importar Extrato"; st.rerun()\n    if q3.button("Ver DAS", use_container_width=True): st.session_state.nav_page="DAS"; st.rerun()\n    if q4.button("Obrigações", use_container_width=True): st.session_state.nav_page="Obrigações"; st.rerun()\n'''
if marker in s and 'Importar extrato", use_container_width=True' not in s:
    s = s.replace(marker, quick, 1)

# Página Importar Extrato
insert_before = 'elif page == "Fluxo de Caixa":\n'
import_page = '''elif page == "Importar Extrato":\n    header("Importar Extrato","Importe CSV ou Excel, confira as colunas e transforme movimentações bancárias em lançamentos do Razync Pro.")\n    st.info("A importação não altera nada até você revisar os dados e confirmar. O sistema também tenta evitar lançamentos duplicados.")\n    uploaded_stmt = st.file_uploader("Extrato bancário", type=["csv","txt","xlsx","xls"], key="bank_statement")\n    if uploaded_stmt is not None:\n        try:\n            raw_stmt = read_statement(uploaded_stmt)\n            st.caption(f"{len(raw_stmt)} linha(s) lidas • {len(raw_stmt.columns)} coluna(s)")\n            st.dataframe(raw_stmt.head(20), use_container_width=True, hide_index=True)\n            cols = list(raw_stmt.columns)\n            a,b,c = st.columns(3)\n            date_col = a.selectbox("Coluna de data", cols)\n            desc_col = b.selectbox("Coluna de descrição/histórico", cols, index=min(1,len(cols)-1))\n            value_col = c.selectbox("Coluna de valor", cols, index=min(2,len(cols)-1))\n            direction = st.radio("Como interpretar o valor", ["Sinal do valor","Tudo como receita","Tudo como despesa"], horizontal=True)\n            prepared = prepare_statement(raw_stmt, date_col, desc_col, value_col, direction)\n            if prepared.empty:\n                st.warning("Nenhuma movimentação válida foi identificada com esse mapeamento.")\n            else:\n                prepared["Duplicado provável"] = [is_probable_duplicate(transactions, r["Data"], r["Tipo"], r["Descrição"], r["Valor"]) for _,r in prepared.iterrows()]\n                prepared["Categoria sugerida"] = [suggest_category(r["Descrição"],r["Tipo"]) for _,r in prepared.iterrows()]\n                st.subheader("Prévia da importação")\n                st.dataframe(prepared, use_container_width=True, hide_index=True, column_config={"Valor":st.column_config.NumberColumn("Valor",format="R$ %.2f")})\n                only_new = prepared[~prepared["Duplicado provável"]].copy()\n                st.caption(f"{len(only_new)} lançamento(s) novo(s) • {int(prepared['Duplicado provável'].sum())} duplicado(s) provável(is) ignorado(s)")\n                if st.button("Importar lançamentos novos", type="primary", use_container_width=True, disabled=only_new.empty):\n                    imported = 0\n                    for _,r in only_new.iterrows():\n                        add_transaction(uid, tx_date=r["Data"], tx_type=r["Tipo"], description=r["Descrição"] or "Movimentação bancária", category=r["Categoria sugerida"], value=float(r["Valor"]), document_number="", counterparty="", payment_method="Conta bancária")\n                        imported += 1\n                    st.success(f"{imported} lançamento(s) importado(s).")\n                    st.session_state.nav_page="Movimentações"\n                    st.rerun()\n        except Exception as exc:\n            st.error(f"Não foi possível ler esse extrato: {exc}")\n\n'''+insert_before
if insert_before in s and 'elif page == "Importar Extrato"' not in s:
    s = s.replace(insert_before, import_page, 1)

# Central automática de obrigações, antes do formulário manual.
ob_marker = '''elif page == "Obrigações":\n    header("Obrigações","Agenda de tarefas fiscais, financeiras, trabalhistas e documentais.")\n'''
ob_new = ob_marker + '''    st.subheader("Calendário automático do MEI")\n    ob_year = st.selectbox("Ano do calendário automático", list(range(CURRENT_YEAR-1,CURRENT_YEAR+2))[::-1], key="auto_ob_year")\n    auto_rows = pd.DataFrame(automatic_obligations(int(ob_year), opening))\n    if not auto_rows.empty:\n        today_value = date.today()\n        upcoming = auto_rows[auto_rows["Vencimento"] >= today_value].sort_values("Vencimento").head(6)\n        c1,c2,c3 = st.columns(3)\n        c1.metric("Obrigações automáticas", len(auto_rows))\n        c2.metric("Vencidas", int((auto_rows["Status automático"]=="Vencida").sum()))\n        c3.metric("Próximas 7 dias", int((auto_rows["Status automático"]=="Próxima").sum()))\n        st.dataframe(auto_rows, use_container_width=True, hide_index=True, column_config={"Vencimento":st.column_config.DateColumn("Vencimento",format="DD/MM/YYYY")})\n        if not upcoming.empty:\n            next_row = upcoming.iloc[0]\n            st.info(f"Próxima obrigação: {next_row['Obrigação']} em {next_row['Vencimento'].strftime('%d/%m/%Y')}.")\n    st.divider()\n    st.subheader("Tarefas personalizadas")\n'''
if ob_marker in s and 'Calendário automático do MEI' not in s:
    s = s.replace(ob_marker, ob_new, 1)

# Melhora Meu MEI exibindo teto oficial do ano seguinte.
mei_info = '''    st.info(f"Limite monitorado para {CURRENT_YEAR}: {brl(annual_limit_for(opening,CURRENT_YEAR,profile.get('annual_limit')))}.")\n'''
mei_info_new = mei_info + '''    st.caption(f"Referência automática do próximo ano: {brl(annual_limit_for(opening,CURRENT_YEAR+1,profile.get('annual_limit')))}. Regras ficam centralizadas no módulo fiscal para atualização anual.")\n'''
if mei_info in s and 'Referência automática do próximo ano' not in s:
    s = s.replace(mei_info, mei_info_new, 1)

p.write_text(s, encoding='utf-8')
print('operations upgrade applied')
