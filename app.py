from __future__ import annotations

from datetime import date
import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    add_contact, add_employee, add_invoice, add_obligation, add_transaction,
    authenticate, create_user, delete_contact, delete_document, delete_employee,
    delete_invoice, delete_obligation, delete_transaction, get_document, get_profile,
    init_db, list_contacts, list_das, list_documents, list_employees, list_invoices,
    list_obligations, list_transactions, save_document, save_profile,
    update_obligation_status, upsert_das, link_transaction_document,
)
from database import database_runtime_info
from fiscal_rules import (
    MEI_ANNUAL_LIMIT, annual_limit_for, build_alerts, competence_list,
    das_due_date, das_status,
)
from reports import dasn_summary_pdf, monthly_report_pdf, financial_summary_pdf, closing_summary_pdf
from bank_import import read_statement, prepare_statement, is_probable_duplicate, suggest_category
from mei_obligations import automatic_obligations
from business_tools import monthly_closing, financial_analysis, consistency_checks
from product_core import NAV_GROUPS, group_for_page, action_items, reconciliation_summary, assistant_answer
from backup_tools import build_backup_zip, document_coverage
from onboarding_tools import onboarding_progress, recommended_setup
from reconciliation_tools import smart_invoice_matches, duplicate_groups
from ui_system import inject_design_system, page_header, section, business_card, alert_card, empty_state, helper_note, apply_plot_theme, tokens

CURRENT_YEAR = date.today().year

st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
init_db()

if "ui_theme" not in st.session_state:
    st.session_state["ui_theme"] = "Claro"

UI_THEME = st.session_state["ui_theme"]
PLOT_TEMPLATE = tokens(UI_THEME)["plot"]
inject_design_system(UI_THEME)


def themed_plotly_chart(fig, *args, **kwargs):
    """Render any Plotly figure using the active Razync theme."""
    apply_plot_theme(fig, UI_THEME)
    config = kwargs.get("config") or {}
    config.setdefault("displayModeBar", False)
    config.setdefault("responsive", True)
    kwargs["config"] = config
    return st.plotly_chart(fig, *args, **kwargs)


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def header(title: str, subtitle: str) -> None:
    page_header(title, subtitle)


def alert_box(level: str, title: str, text: str) -> None:
    alert_card(level, title, text)


def ensure_login() -> dict:
    email = "dev@local"
    password = "dev"
    user = authenticate(email, password)
    if not user:
        create_user("Desenvolvimento", email, password)
        user = authenticate(email, password)
    if not user:
        st.stop()
    st.session_state.user = user
    return user

def tx_df(uid: int) -> pd.DataFrame:
    df = pd.DataFrame(list_transactions(uid))
    if df.empty:
        return pd.DataFrame(columns=["id","tx_date","tx_type","description","category","value","document_number","counterparty","payment_method"])
    df["tx_date"] = pd.to_datetime(df["tx_date"])
    return df


def invoice_df(uid: int) -> pd.DataFrame:
    df = pd.DataFrame(list_invoices(uid))
    if not df.empty:
        df["issue_date"] = pd.to_datetime(df["issue_date"])
    return df


def opening_date_from(profile: dict) -> date | None:
    value = profile.get("opening_date")
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def monthly_rows(df: pd.DataFrame, year: int) -> list[dict]:
    rows = []
    for month in range(1,13):
        cur = df[(df["tx_type"]=="Receita") & (df["tx_date"].dt.year==year) & (df["tx_date"].dt.month==month)] if not df.empty else df
        if cur.empty:
            services = sales = with_doc = without_doc = total = 0.0
        else:
            services = float(cur[cur["category"].isin(["Serviços","Serviço"])]["value"].sum())
            total = float(cur["value"].sum())
            sales = total - services
            has_doc = cur["document_number"].fillna("").astype(str).str.strip().ne("")
            with_doc = float(cur.loc[has_doc,"value"].sum())
            without_doc = total - with_doc
        rows.append({"month":month,"month_name":calendar.month_name[month],"with_doc":with_doc,"without_doc":without_doc,"services":services,"sales":sales,"total":total})
    return rows


def category_totals_for_dasn(df: pd.DataFrame, year: int) -> tuple[float,float]:
    if df.empty:
        return 0.0,0.0
    cur = df[(df["tx_type"]=="Receita") & (df["tx_date"].dt.year==year)]
    services = float(cur[cur["category"].isin(["Serviços","Serviço"])]["value"].sum())
    sales = float(cur["value"].sum()) - services
    return services, sales


def cashflow_monthly(df: pd.DataFrame, year: int) -> pd.DataFrame:
    rows = []
    for month in range(1, 13):
        cur = df[df["tx_date"].dt.year == year] if not df.empty else df
        cur = cur[cur["tx_date"].dt.month == month] if not cur.empty else cur
        entradas = float(cur[cur["tx_type"] == "Receita"]["value"].sum()) if not cur.empty else 0.0
        saidas = float(cur[cur["tx_type"] == "Despesa"]["value"].sum()) if not cur.empty else 0.0
        rows.append({"Mês": calendar.month_name[month], "Entradas": entradas, "Saídas": saidas, "Resultado": entradas-saidas})
    out = pd.DataFrame(rows)
    out["Saldo acumulado"] = out["Resultado"].cumsum()
    return out

def mei_health_score(profile: dict, revenue: float, limit: float, das_rows: list, obligations: list) -> tuple[int, list[str]]:
    score = 100
    notes = []
    if not profile.get("cnpj"):
        score -= 20; notes.append("Complete os dados do CNPJ em Meu MEI.")
    if not profile.get("main_activity"):
        score -= 10; notes.append("Informe a atividade principal.")
    if limit and revenue / limit >= 0.8:
        score -= 20; notes.append("Faturamento acima de 80% do limite monitorado.")
    overdue = [d for d in das_rows if das_status(d.get("status", "Pendente"), d.get("due_date")) == "Atrasado"]
    if overdue:
        score -= min(30, len(overdue) * 10); notes.append(f"Existem {len(overdue)} DAS em atraso.")
    late_obs = [o for o in obligations if o.get("status") != "Concluído" and o.get("due_date") and o.get("due_date") < date.today()]
    if late_obs:
        score -= min(20, len(late_obs) * 5); notes.append(f"Existem {len(late_obs)} obrigações vencidas.")
    return max(score, 0), notes


user = ensure_login()
uid = int(user["id"])
profile = get_profile(uid)
transactions = tx_df(uid)
invoices = invoice_df(uid)
das_rows = list_das(uid)
docs = list_documents(uid)
employees = list_employees(uid)
contacts = list_contacts(uid)
obligations = list_obligations(uid)

pending_page = st.session_state.pop("_navigate_to", None)
if pending_page:
    st.session_state["_current_page"] = pending_page

page = st.session_state.get("_current_page", "Dashboard")
all_pages = [p for pages in NAV_GROUPS.values() for p in pages]
if page not in all_pages:
    page = "Dashboard"
    st.session_state["_current_page"] = page

with st.sidebar:
    st.markdown('<div class="rz-brand-wrap"><div class="rz-brand">RAZYNC <span>PRO</span></div><div class="rz-brand-sub">Contabilidade simples para MEI</div></div>', unsafe_allow_html=True)
    st.selectbox("Tema", ["Claro", "Escuro"], key="ui_theme")
    st.markdown('<div class="rz-sidebar-section">Navegação</div>', unsafe_allow_html=True)

    if page == "Dashboard":
        st.markdown('<div class="rz-current-page">⌂  Início</div>', unsafe_allow_html=True)
    elif st.button("⌂  Início", key="nav_home", use_container_width=True):
        st.session_state["_navigate_to"] = "Dashboard"
        st.rerun()

    sidebar_groups = {
        "Financeiro": NAV_GROUPS["Financeiro"],
        "Fiscal MEI": NAV_GROUPS["Fiscal MEI"],
        "Gestão": NAV_GROUPS["Gestão"],
        "Relatórios": NAV_GROUPS["Relatórios"],
        "Configurações": NAV_GROUPS["Configurações"],
    }
    icons = {"Financeiro":"▰", "Fiscal MEI":"▣", "Gestão":"◇", "Relatórios":"▤", "Configurações":"⚙"}
    current_group = group_for_page(page)
    for group, pages in sidebar_groups.items():
        with st.expander(f"{icons[group]}  {group}", expanded=(current_group == group)):
            for nav_page in pages:
                if nav_page == page:
                    st.markdown(f'<div class="rz-current-page">{nav_page}</div>', unsafe_allow_html=True)
                elif st.button(nav_page, key=f"nav_{group}_{nav_page}", use_container_width=True):
                    st.session_state["_navigate_to"] = nav_page
                    st.rerun()
    st.markdown('<div class="rz-dev">Desenvolvimento • acesso direto</div>', unsafe_allow_html=True)

opening = opening_date_from(profile)
limit = annual_limit_for(opening, CURRENT_YEAR, profile.get("annual_limit"))
year_tx = transactions[(transactions["tx_date"].dt.year==CURRENT_YEAR)] if not transactions.empty else transactions
year_revenue = float(year_tx[year_tx["tx_type"]=="Receita"]["value"].sum()) if not year_tx.empty else 0.0
year_expense = float(year_tx[year_tx["tx_type"]=="Despesa"]["value"].sum()) if not year_tx.empty else 0.0
limit_pct = (year_revenue/limit*100) if limit else 0.0

if page == "Dashboard":
    business_label = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"
    cnpj_label = str(profile.get("cnpj") or "").strip() or None
    page_header("Visão geral", "Seu financeiro e suas obrigações em uma tela, com foco no que precisa de ação agora.")
    business_card(business_label, CURRENT_YEAR, cnpj_label)
    onboarding = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))
    if not onboarding["complete"]:
        st.info(f"Configuração inicial: {onboarding['done']} de {onboarding['total']} etapas concluídas ({onboarding['percent']}%).")
        if st.button("Continuar configuração do MEI", key="dash_onboarding", use_container_width=True):
            st.session_state["_navigate_to"] = "Primeiros Passos"
            st.rerun()

    today = date.today()
    month_tx = transactions[(transactions["tx_date"].dt.year == CURRENT_YEAR) & (transactions["tx_date"].dt.month == today.month)] if not transactions.empty else transactions
    month_in = float(month_tx[month_tx["tx_type"] == "Receita"]["value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx[month_tx["tx_type"] == "Despesa"]["value"].sum()) if not month_tx.empty else 0.0
    month_result = month_in - month_out

    section("Resumo financeiro", "Valores do mês atual e faturamento acumulado no ano.")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Entradas no mês", brl(month_in))
    k2.metric("Saídas no mês", brl(month_out))
    k3.metric("Resultado do mês", brl(month_result))
    k4.metric("Faturamento no ano", brl(year_revenue))

    action_col, quick_col = st.columns([1.72, 1], gap="large")
    priorities = action_items(profile, transactions, invoices, das_rows, obligations, limit, year_revenue)
    with action_col:
        section("Centro de ação", "Pendências priorizadas pelo Razync Pro.")
        for idx, item in enumerate(priorities[:3]):
            row, btn = st.columns([4.8,1.15])
            with row:
                level = "danger" if item["priority"] == 1 else "warn" if item["priority"] == 2 else "info" if item["priority"] == 3 else "ok"
                alert_card(level, item["title"], item["detail"])
            with btn:
                if item["page"] != "Dashboard" and st.button("Resolver", key=f"priority_{idx}", use_container_width=True):
                    st.session_state["_navigate_to"] = item["page"]
                    st.rerun()
    with quick_col:
        section("Acesso rápido", "As ações mais usadas no dia a dia.")
        if st.button("＋ Nova movimentação", key="dash_new_tx", use_container_width=True):
            st.session_state["_navigate_to"] = "Movimentações"; st.rerun()
        if st.button("↥ Importar extrato", key="dash_import", use_container_width=True):
            st.session_state["_navigate_to"] = "Importar Extrato"; st.rerun()
        if st.button("▣ Impostos e DAS", key="dash_fiscal", use_container_width=True):
            st.session_state["_navigate_to"] = "Central Fiscal"; st.rerun()
        if st.button("✓ Obrigações", key="dash_oblig", use_container_width=True):
            st.session_state["_navigate_to"] = "Obrigações"; st.rerun()

    chart_col, status_col = st.columns([1.65,1], gap="large")
    with chart_col:
        section("Evolução do faturamento", "Receitas registradas mês a mês no ano atual.")
        chart = pd.DataFrame(monthly_rows(transactions, CURRENT_YEAR))
        fig = px.area(chart, x="month_name", y="total", markers=True)
        apply_plot_theme(fig, UI_THEME, height=320)
        fig.update_traces(line=dict(width=2.4), fillcolor="rgba(37,99,235,.10)")
        fig.update_xaxes(title="", showgrid=False)
        fig.update_yaxes(title="", gridcolor=tokens(UI_THEME)["border"])
        themed_plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with status_col:
        section("Situação do MEI", "Limite, DAS e nível de organização.")
        health_score, health_notes = mei_health_score(profile, year_revenue, limit, das_rows, obligations)
        s1,s2 = st.columns(2)
        s1.metric("Limite usado", f"{limit_pct:.1f}%")
        overdue_das = sum(1 for d in das_rows if das_status(d.get("status", "Pendente"), d.get("due_date")) == "Atrasado")
        s2.metric("DAS atrasado", overdue_das)
        st.caption(f"Limite monitorado: {brl(limit)} • restante: {brl(max(limit-year_revenue,0))}")
        st.progress(min(max(limit_pct/100, 0), 1.0))
        st.caption(f"Índice de organização: {health_score}/100")
        st.progress(health_score/100)
        if health_notes:
            for note in health_notes[:2]: st.caption(f"• {note}")

    section("Movimentações recentes", "Últimos registros financeiros adicionados ao sistema.")
    if transactions.empty:
        st.info("Ainda não há movimentações. Use “Nova movimentação” ou importe um extrato para começar.")
    else:
        recent = transactions.sort_values("tx_date", ascending=False).head(8)
        st.dataframe(
            recent[["tx_date","tx_type","description","counterparty","value"]],
            use_container_width=True, hide_index=True,
            column_config={
                "tx_date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "tx_type": "Tipo", "description": "Descrição", "counterparty": "Cliente/fornecedor",
                "value": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            },
        )

    with st.expander("Configuração inicial do MEI", expanded=not bool(profile.get("cnpj"))):
        checklist = [
            ("CNPJ cadastrado", bool(profile.get("cnpj"))),
            ("Atividade principal informada", bool(profile.get("main_activity"))),
            ("Data de abertura cadastrada", bool(profile.get("opening_date"))),
            ("Primeira movimentação registrada", not transactions.empty),
            ("Calendário do DAS criado", bool(das_rows)),
            ("Documento armazenado", bool(docs)),
        ]
        done_count = sum(1 for _, done in checklist if done)
        st.caption(f"{done_count} de {len(checklist)} etapas concluídas")
        st.progress(done_count/len(checklist))
        for label, done in checklist:
            st.write(("✓ " if done else "○ ") + label)

elif page == "Movimentações":
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

elif page == "Importar Extrato":
    header("Importar Extrato","Importe CSV ou Excel, confira as colunas e transforme movimentações bancárias em lançamentos do Razync Pro.")
    st.info("A importação não altera nada até você revisar os dados e confirmar. O sistema também tenta evitar lançamentos duplicados.")
    uploaded_stmt = st.file_uploader("Extrato bancário", type=["csv","txt","xlsx","xls"], key="bank_statement")
    if uploaded_stmt is not None:
        try:
            raw_stmt = read_statement(uploaded_stmt)
            st.caption(f"{len(raw_stmt)} linha(s) lidas • {len(raw_stmt.columns)} coluna(s)")
            st.dataframe(raw_stmt.head(20), use_container_width=True, hide_index=True)
            cols = list(raw_stmt.columns)
            a,b,c = st.columns(3)
            date_col = a.selectbox("Coluna de data", cols)
            desc_col = b.selectbox("Coluna de descrição/histórico", cols, index=min(1,len(cols)-1))
            value_col = c.selectbox("Coluna de valor", cols, index=min(2,len(cols)-1))
            direction = st.radio("Como interpretar o valor", ["Sinal do valor","Tudo como receita","Tudo como despesa"], horizontal=True)
            prepared = prepare_statement(raw_stmt, date_col, desc_col, value_col, direction)
            if prepared.empty:
                st.warning("Nenhuma movimentação válida foi identificada com esse mapeamento.")
            else:
                prepared["Duplicado provável"] = [is_probable_duplicate(transactions, r["Data"], r["Tipo"], r["Descrição"], r["Valor"]) for _,r in prepared.iterrows()]
                prepared["Categoria sugerida"] = [suggest_category(r["Descrição"],r["Tipo"]) for _,r in prepared.iterrows()]
                st.subheader("Prévia da importação")
                st.dataframe(prepared, use_container_width=True, hide_index=True, column_config={"Valor":st.column_config.NumberColumn("Valor",format="R$ %.2f")})
                only_new = prepared[~prepared["Duplicado provável"]].copy()
                st.caption(f"{len(only_new)} lançamento(s) novo(s) • {int(prepared['Duplicado provável'].sum())} duplicado(s) provável(is) ignorado(s)")
                if st.button("Importar lançamentos novos", type="primary", use_container_width=True, disabled=only_new.empty):
                    imported = 0
                    for _,r in only_new.iterrows():
                        add_transaction(uid, tx_date=r["Data"], tx_type=r["Tipo"], description=r["Descrição"] or "Movimentação bancária", category=r["Categoria sugerida"], value=float(r["Valor"]), document_number="", counterparty="", payment_method="Conta bancária")
                        imported += 1
                    st.success(f"{imported} lançamento(s) importado(s).")
                    st.session_state["_navigate_to"]="Movimentações"
                    st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível ler esse extrato: {exc}")

elif page == "Conciliação":
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

elif page == "Fluxo de Caixa":
    header("Fluxo de Caixa","Acompanhe entradas, saídas, resultado mensal e evolução do saldo do negócio.")
    years = {CURRENT_YEAR}
    if not transactions.empty:
        years.update(int(y) for y in transactions["tx_date"].dt.year.unique())
    flow_year = st.selectbox("Ano do fluxo de caixa", sorted(years, reverse=True))
    flow = cashflow_monthly(transactions, int(flow_year))
    c1,c2,c3 = st.columns(3)
    c1.metric("Entradas", brl(float(flow["Entradas"].sum())))
    c2.metric("Saídas", brl(float(flow["Saídas"].sum())))
    c3.metric("Resultado", brl(float(flow["Resultado"].sum())))
    chart = flow.melt(id_vars=["Mês"], value_vars=["Entradas","Saídas"], var_name="Tipo", value_name="Valor")
    fig = px.bar(chart, x="Mês", y="Valor", color="Tipo", barmode="group")
    fig.update_layout(template=PLOT_TEMPLATE,height=350, margin=dict(l=0,r=0,t=10,b=0), xaxis_title="", yaxis_title="Valor")
    themed_plotly_chart(fig, use_container_width=True)
    fig2 = px.line(flow, x="Mês", y="Saldo acumulado", markers=True)
    fig2.update_layout(template=PLOT_TEMPLATE,height=300, margin=dict(l=0,r=0,t=10,b=0), xaxis_title="", yaxis_title="Saldo acumulado")
    themed_plotly_chart(fig2, use_container_width=True)
    st.dataframe(flow, use_container_width=True, hide_index=True, column_config={c:st.column_config.NumberColumn(c, format="R$ %.2f") for c in ["Entradas","Saídas","Resultado","Saldo acumulado"]})

elif page == "Análise Financeira":
    header("Análise Financeira","Entenda resultado, margem e principais gastos do seu MEI.")
    years = {CURRENT_YEAR}
    if not transactions.empty:
        years.update(int(y) for y in transactions["tx_date"].dt.year.unique())
    analysis_year = st.selectbox("Ano da análise", sorted(years, reverse=True), key="analysis_year")
    analysis = financial_analysis(transactions, int(analysis_year))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Receitas", brl(analysis["revenue"]))
    c2.metric("Despesas", brl(analysis["expenses"]))
    c3.metric("Resultado", brl(analysis["result"]))
    c4.metric("Margem estimada", f"{analysis['margin']:.1f}%")
    left,right = st.columns([1.4,1])
    with left:
        monthly = analysis["monthly"]
        if not monthly.empty:
            chart = monthly.melt(id_vars=["Mês"], value_vars=["Receitas","Despesas"], var_name="Tipo", value_name="Valor")
            fig = px.bar(chart, x="Mês", y="Valor", color="Tipo", barmode="group")
            fig.update_layout(template=PLOT_TEMPLATE,height=340, margin=dict(l=0,r=0,t=8,b=0), xaxis_title="Mês", yaxis_title="Valor")
            themed_plotly_chart(fig, use_container_width=True)
    with right:
        exp = analysis["expense_categories"]
        if exp.empty:
            empty_state("Sem despesas no período", "Quando houver despesas registradas, a distribuição por categoria aparecerá aqui.", "◫")
        else:
            fig = px.pie(exp, names="Categoria", values="Valor", hole=.45)
            fig.update_layout(template=PLOT_TEMPLATE,height=340, margin=dict(l=0,r=0,t=8,b=0))
            themed_plotly_chart(fig, use_container_width=True)
    st.subheader("Verificações de consistência")
    checks = pd.DataFrame(consistency_checks(transactions, invoices, das_rows))
    st.dataframe(checks, use_container_width=True, hide_index=True)

elif page == "Central Fiscal":
    header("Central Fiscal MEI","Uma visão única do limite, DAS, relatório mensal, DASN-SIMEI e obrigações.")
    overdue_das = [d for d in das_rows if das_status(d.get("status","Pendente"), d.get("due_date")) == "Atrasado"]
    pending_das = [d for d in das_rows if das_status(d.get("status","Pendente"), d.get("due_date")) == "Pendente"]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Faturamento no ano", brl(year_revenue))
    c2.metric("Limite restante", brl(max(limit-year_revenue,0)))
    c3.metric("DAS em atraso", len(overdue_das))
    c4.metric("DAS pendentes", len(pending_das))
    st.progress(min(limit_pct/100, 1.0))
    st.caption(f"{limit_pct:.1f}% do limite monitorado utilizado.")

    st.subheader("Próximas obrigações")
    auto = pd.DataFrame(automatic_obligations(CURRENT_YEAR, opening))
    if not auto.empty:
        future = auto[auto["Vencimento"] >= date.today()].sort_values("Vencimento").head(6)
        st.dataframe(future, use_container_width=True, hide_index=True, column_config={"Vencimento":st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY")})

    st.subheader("Acessos fiscais")
    a,b,c,d = st.columns(4)
    if a.button("DAS", use_container_width=True): st.session_state["_navigate_to"]="DAS"; st.rerun()
    if b.button("Relatório Mensal", use_container_width=True): st.session_state["_navigate_to"]="Relatório Mensal"; st.rerun()
    if c.button("DASN-SIMEI", use_container_width=True): st.session_state["_navigate_to"]="DASN-SIMEI"; st.rerun()
    if d.button("Obrigações", use_container_width=True): st.session_state["_navigate_to"]="Obrigações"; st.rerun()
    st.info("O Razync Pro organiza e confere os dados. Envios e pagamentos oficiais continuam nos serviços governamentais correspondentes.")

elif page == "Fechamento Mensal":
    header("Fechamento Mensal","Revise receitas, despesas, notas, documentos e DAS antes de considerar o mês organizado.")
    years = {CURRENT_YEAR}
    if not transactions.empty:
        years.update(int(y) for y in transactions["tx_date"].dt.year.unique())
    a,b = st.columns(2)
    close_year = a.selectbox("Ano", sorted(years, reverse=True), key="close_year")
    close_month = b.selectbox("Mês", list(range(1,13)), index=max(date.today().month-1,0), key="close_month")
    closing = monthly_closing(transactions, invoices, docs, das_rows, int(close_year), int(close_month))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Receitas", brl(closing["revenue"]))
    c2.metric("Despesas", brl(closing["expenses"]))
    c3.metric("Resultado", brl(closing["result"]))
    c4.metric("Organização do mês", f"{closing['score']}%")
    st.progress(closing["score"]/100)
    checklist = pd.DataFrame(closing["checklist"])
    checklist["Status"] = checklist["OK"].map({True:"OK", False:"Pendente"})
    st.dataframe(checklist[["Item","Status","Detalhe"]], use_container_width=True, hide_index=True)
    if abs(closing["invoice_difference"]) > 0.01:
        st.warning(f"A receita registrada difere do total de notas emitidas no mês em {brl(abs(closing['invoice_difference']))}. Revise antes do fechamento.")
    if closing["das_status"] == "Atrasado":
        st.error("O DAS desta competência está em atraso.")
    elif closing["das_status"] == "Não criado":
        st.warning("O calendário do DAS ainda não possui esta competência.")
    else:
        st.info(f"Situação do DAS: {closing['das_status']}.")
    month_csv = closing["transactions"].to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar movimentações do mês", month_csv, f"fechamento_{close_year}_{int(close_month):02d}.csv", "text/csv", use_container_width=True)

elif page == "Relatório Mensal":
    header("Relatório Mensal de Receitas Brutas","Consolidação automática com receitas documentadas, não documentadas, serviços e vendas.")
    years = {CURRENT_YEAR}; years.update(int(y) for y in transactions["tx_date"].dt.year.unique()) if not transactions.empty else None
    selected_year = st.selectbox("Ano",sorted(years,reverse=True))
    rows = monthly_rows(transactions,int(selected_year)); rdf = pd.DataFrame(rows)
    show = rdf.rename(columns={"month_name":"Mês","with_doc":"Com documento","without_doc":"Sem documento","services":"Serviços","sales":"Vendas","total":"Receita bruta"})
    st.dataframe(show[["Mês","Com documento","Sem documento","Serviços","Vendas","Receita bruta"]],use_container_width=True,hide_index=True,column_config={c:st.column_config.NumberColumn(c,format="R$ %.2f") for c in ["Com documento","Sem documento","Serviços","Vendas","Receita bruta"]})
    c1,c2,c3 = st.columns(3); c1.metric("Receita no ano",brl(float(rdf["total"].sum()))); c2.metric("Com documento",brl(float(rdf["with_doc"].sum()))); c3.metric("Sem documento",brl(float(rdf["without_doc"].sum())))
    pdf = monthly_report_pdf(profile,int(selected_year),rows); csv = show.to_csv(index=False).encode("utf-8-sig")
    a,b = st.columns(2); a.download_button("Baixar relatório em PDF",pdf,f"relatorio_mensal_{selected_year}.pdf","application/pdf",use_container_width=True); b.download_button("Baixar relatório em CSV",csv,f"relatorio_mensal_{selected_year}.csv","text/csv",use_container_width=True)

elif page == "Notas Fiscais":
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

elif page == "DAS":
    header("DAS","Calendário por competência, vencimento, pagamento e atraso automático.")
    year = st.selectbox("Ano do calendário",list(range(CURRENT_YEAR-3,CURRENT_YEAR+2))[::-1]); existing = {str(d["competence"]):d for d in das_rows}
    if st.button("Gerar/atualizar calendário anual",type="primary"):
        for comp in competence_list(int(year)):
            if comp not in existing: upsert_das(uid,comp,das_due_date(comp),0.0,"Pendente",None,"")
        st.rerun()
    ddf = pd.DataFrame(list_das(uid))
    if not ddf.empty:
        ddf = ddf[ddf["competence"].astype(str).str.startswith(str(year))].copy()
        if not ddf.empty:
            ddf["status_atual"] = [das_status(r["status"],r["due_date"]) for _,r in ddf.iterrows()]
            st.dataframe(ddf[["competence","due_date","amount","status_atual","payment_date","notes"]],use_container_width=True,hide_index=True,column_config={"due_date":st.column_config.DateColumn("Vencimento",format="DD/MM/YYYY"),"amount":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"payment_date":st.column_config.DateColumn("Pagamento",format="DD/MM/YYYY")})
        else:
            empty_state("Calendário ainda não criado", "Gere o calendário anual para acompanhar vencimentos e pagamentos do DAS por competência.", "▣")
    st.subheader("Atualizar competência")
    with st.form("das_update"):
        comp = st.selectbox("Competência",competence_list(int(year))); current = existing.get(comp,{}); due = st.date_input("Vencimento",value=current.get("due_date") or das_due_date(comp)); amount = st.number_input("Valor do DAS",min_value=0.0,value=float(current.get("amount") or 0),step=1.0)
        options=["Pendente","Pago","Atrasado"]; current_status=current.get("status","Pendente"); status=st.selectbox("Situação",options,index=options.index(current_status) if current_status in options else 0); payment_date=st.date_input("Data do pagamento",value=current.get("payment_date") or date.today()) if status=="Pago" else None; notes=st.text_input("Observações",value=str(current.get("notes") or ""))
        if st.form_submit_button("Salvar competência",type="primary"): upsert_das(uid,comp,due,float(amount),status,payment_date,notes); st.rerun()

elif page == "DASN-SIMEI":
    header("DASN-SIMEI","Conferência anual automática das receitas cadastradas.")
    year = st.selectbox("Ano-calendário",list(range(CURRENT_YEAR-5,CURRENT_YEAR+1))[::-1]); services,sales = category_totals_for_dasn(transactions,int(year)); total = services+sales; active_employee = any(e.get("status")=="Ativo" for e in employees)
    c1,c2,c3,c4 = st.columns(4); c1.metric("Serviços",brl(services)); c2.metric("Comércio/mercadorias",brl(sales)); c3.metric("Receita bruta total",brl(total)); c4.metric("Teve empregado","Sim" if active_employee else "Não")
    if total == 0: st.info("Nenhuma receita foi registrada para este ano. A declaração anual pode continuar sendo necessária mesmo sem faturamento.")
    pdf = dasn_summary_pdf(profile,int(year),services,sales,active_employee); summary = pd.DataFrame([{"ano":year,"servicos":services,"comercio_mercadorias":sales,"receita_bruta_total":total,"teve_empregado":active_employee}])
    a,b = st.columns(2); a.download_button("Baixar resumo em PDF",pdf,f"dasn_{year}_conferencia.pdf","application/pdf",use_container_width=True); b.download_button("Baixar resumo em CSV",summary.to_csv(index=False).encode("utf-8-sig"),f"dasn_{year}_conferencia.csv","text/csv",use_container_width=True)
    st.caption("O Razync Pro prepara e confere os dados; o envio oficial da DASN-SIMEI continua sendo feito no serviço oficial.")

elif page == "Obrigações":
    header("Obrigações","Agenda de tarefas fiscais, financeiras, trabalhistas e documentais.")
    st.subheader("Calendário automático do MEI")
    ob_year = st.selectbox("Ano do calendário automático", list(range(CURRENT_YEAR-1,CURRENT_YEAR+2))[::-1], key="auto_ob_year")
    auto_rows = pd.DataFrame(automatic_obligations(int(ob_year), opening))
    if not auto_rows.empty:
        today_value = date.today()
        upcoming = auto_rows[auto_rows["Vencimento"] >= today_value].sort_values("Vencimento").head(6)
        c1,c2,c3 = st.columns(3)
        c1.metric("Obrigações automáticas", len(auto_rows))
        c2.metric("Vencidas", int((auto_rows["Status automático"]=="Vencida").sum()))
        c3.metric("Próximas 7 dias", int((auto_rows["Status automático"]=="Próxima").sum()))
        st.dataframe(auto_rows, use_container_width=True, hide_index=True, column_config={"Vencimento":st.column_config.DateColumn("Vencimento",format="DD/MM/YYYY")})
        if not upcoming.empty:
            next_row = upcoming.iloc[0]
            st.info(f"Próxima obrigação: {next_row['Obrigação']} em {next_row['Vencimento'].strftime('%d/%m/%Y')}.")
    st.divider()
    st.subheader("Tarefas personalizadas")
    with st.form("ob_form",clear_on_submit=True):
        a,b,c=st.columns(3); title=a.text_input("Obrigação/tarefa"); due_date=b.date_input("Vencimento",date.today()); category=c.selectbox("Categoria",["Fiscal","Financeira","Trabalhista","Documental","Outra"]); notes=st.text_input("Observações")
        if st.form_submit_button("Adicionar",type="primary") and title.strip(): add_obligation(uid,title=title.strip(),due_date=due_date,category=category,notes=notes); st.rerun()
    odf=pd.DataFrame(list_obligations(uid))
    if odf.empty: empty_state("Nenhuma tarefa personalizada", "O calendário automático continua funcionando. Crie uma tarefa aqui apenas quando precisar acompanhar algo específico do seu MEI.", "✓")
    else:
        st.dataframe(odf,use_container_width=True,hide_index=True); a,b=st.columns(2); oid=a.selectbox("ID",odf["id"].tolist()); new_status=b.selectbox("Status",["Pendente","Concluído"]); c,d=st.columns(2)
        if c.button("Atualizar status",use_container_width=True): update_obligation_status(uid,int(oid),new_status); st.rerun()
        if d.button("Excluir obrigação",use_container_width=True): delete_obligation(uid,int(oid)); st.rerun()

elif page == "Clientes e Fornecedores":
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

elif page == "Empregado":
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

elif page == "Documentos":
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

elif page == "Central de Relatórios":
    header("Central de Relatórios","Gere documentos gerenciais e fiscais a partir dos dados já cadastrados.")
    years = {CURRENT_YEAR}
    if not transactions.empty:
        years.update(int(y) for y in transactions["tx_date"].dt.year.unique())
    report_year = st.selectbox("Ano", sorted(years, reverse=True), key="report_center_year")
    report_month = st.selectbox("Mês para fechamento", list(range(1,13)), index=max(date.today().month-1,0), key="report_center_month")
    analysis_report = financial_analysis(transactions, int(report_year))
    closing_report = monthly_closing(transactions, invoices, docs, das_rows, int(report_year), int(report_month))
    monthly_data = monthly_rows(transactions, int(report_year))
    services_report, sales_report = category_totals_for_dasn(transactions, int(report_year))
    active_employee_report = any(e.get("status") == "Ativo" for e in employees)

    st.subheader("Relatórios disponíveis")
    r1,r2 = st.columns(2)
    with r1:
        st.download_button("Análise financeira em PDF", financial_summary_pdf(profile, int(report_year), analysis_report), f"analise_financeira_{report_year}.pdf", "application/pdf", use_container_width=True)
        st.download_button("Relatório Mensal em PDF", monthly_report_pdf(profile, int(report_year), monthly_data), f"relatorio_mensal_{report_year}.pdf", "application/pdf", use_container_width=True)
    with r2:
        st.download_button("Fechamento mensal em PDF", closing_summary_pdf(profile, int(report_year), int(report_month), closing_report), f"fechamento_{report_year}_{int(report_month):02d}.pdf", "application/pdf", use_container_width=True)
        st.download_button("Resumo DASN-SIMEI em PDF", dasn_summary_pdf(profile, int(report_year), services_report, sales_report, active_employee_report), f"dasn_{report_year}.pdf", "application/pdf", use_container_width=True)
    st.caption("Todos os relatórios são gerados com base nos dados cadastrados no Razync Pro e devem ser conferidos antes de uso oficial.")

elif page == "Assistente Razync":
    header("Assistente Razync","Pergunte sobre faturamento, despesas, limite, DAS e conciliação usando os dados do seu MEI.")
    st.caption("Sugestões: Quanto posso faturar? • Quanto sobrou? • Quais são meus maiores gastos? • Tenho DAS atrasado? • Existem notas pendentes?")
    question = st.text_input("Pergunte sobre seu MEI", key="assistant_question")
    if question:
        st.info(assistant_answer(question, transactions, invoices, das_rows, limit, CURRENT_YEAR))
    st.divider()
    st.caption("O Assistente Razync usa os dados cadastrados no sistema. Para situações fiscais especiais, desenquadramento ou decisões profissionais, confirme a orientação em fonte oficial ou com profissional habilitado.")

elif page == "Primeiros Passos":
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

elif page == "Meu MEI":
    header("Meu MEI","Dados usados nos cálculos, relatórios e alertas do Razync Pro.")
    with st.form("profile_form"):
        a,b=st.columns(2); business_name=a.text_input("Nome empresarial",value=str(profile.get("business_name") or "")); trade_name=b.text_input("Nome fantasia",value=str(profile.get("trade_name") or "")); a,b=st.columns(2); cnpj=a.text_input("CNPJ",value=str(profile.get("cnpj") or "")); main_activity=b.text_input("Atividade principal",value=str(profile.get("main_activity") or ""))
        a,b,c=st.columns(3); options=["Serviços","Comércio","Indústria","Misto"]; current=profile.get("activity_type","Serviços"); activity_type=a.selectbox("Tipo principal",options,index=options.index(current) if current in options else 0); opening_date=b.date_input("Data de abertura",value=opening or date.today()); annual_limit=c.number_input("Limite anual de referência",min_value=0.0,value=float(profile.get("annual_limit") or MEI_ANNUAL_LIMIT),step=1000.0)
        a,b,c=st.columns(3); phone=a.text_input("Telefone",value=str(profile.get("phone") or "")); city=b.text_input("Cidade",value=str(profile.get("city") or "")); state=c.text_input("UF",value=str(profile.get("state") or ""),max_chars=2); a,b=st.columns(2); municipal_registration=a.text_input("Inscrição municipal",value=str(profile.get("municipal_registration") or "")); state_registration=b.text_input("Inscrição estadual",value=str(profile.get("state_registration") or ""))
        if st.form_submit_button("Salvar dados",type="primary",use_container_width=True): save_profile(uid,business_name=business_name,trade_name=trade_name,cnpj=cnpj,main_activity=main_activity,activity_type=activity_type,opening_date=opening_date,annual_limit=float(annual_limit),phone=phone,city=city,state=state.upper(),municipal_registration=municipal_registration,state_registration=state_registration); st.rerun()
    st.info(f"Limite monitorado para {CURRENT_YEAR}: {brl(annual_limit_for(opening,CURRENT_YEAR,profile.get('annual_limit')))}.")
    st.caption(f"Referência automática do próximo ano: {brl(annual_limit_for(opening,CURRENT_YEAR+1,profile.get('annual_limit')))}. Regras ficam centralizadas no módulo fiscal para atualização anual.")

elif page == "Status do Sistema":
    header("Status do Sistema","Veja o que já está operacional e o que ainda depende de configuração externa.")
    dbinfo = database_runtime_info()
    c1,c2,c3 = st.columns(3)
    c1.metric("Banco de dados", dbinfo["backend"])
    c2.metric("Persistência", "Ativa" if dbinfo["persistent"] else "Temporária")
    c3.metric("Banco de produção", "Pronto" if dbinfo["production_ready"] else "Pendente")
    if dbinfo["persistent"]:
        st.success("O Razync Pro está conectado a PostgreSQL e os dados podem ser mantidos fora do ciclo temporário do Streamlit.")
    else:
        st.warning("O sistema está usando SQLite temporário. Para dados reais, configure DATABASE_URL nos Secrets do Streamlit apontando para PostgreSQL/Supabase.")
    st.subheader("Integrações")
    integration_rows = pd.DataFrame([
        {"Integração":"Importação de extrato CSV/Excel", "Status":"Operacional", "Observação":"Importação com prévia, categorização sugerida e controle de duplicidade."},
        {"Integração":"PostgreSQL / Supabase", "Status":"Operacional" if dbinfo["persistent"] else "Aguardando credencial", "Observação":"Suporte no código concluído; requer DATABASE_URL do banco gerenciado."},
        {"Integração":"NFS-e Nacional", "Status":"Controle manual", "Observação":"Notas podem ser controladas e conciliadas; integração automática depende do fluxo/API oficial aplicável ao emissor."},
        {"Integração":"Assistente Razync", "Status":"Operacional", "Observação":"Consulta faturamento, despesas, limite, DAS e conciliação com base nos dados cadastrados."},
    ])
    st.dataframe(integration_rows, use_container_width=True, hide_index=True)

elif page == "Backup":
    header("Backup e exportação","Baixe uma cópia consolidada ou arquivos separados dos dados cadastrados.")
    backup_zip = build_backup_zip(profile, transactions, invoices, das_rows, contacts, obligations, employees, docs)
    st.download_button("Baixar backup completo (.zip)", backup_zip, f"razync_pro_backup_{date.today().isoformat()}.zip", "application/zip", type="primary", use_container_width=True)
    st.caption("O ZIP contém perfil, movimentações, notas fiscais, DAS, contatos, obrigações, empregados e índice de documentos.")
    st.subheader("Arquivos individuais")
    files={"movimentacoes.csv":transactions.to_csv(index=False).encode("utf-8-sig"),"notas_fiscais.csv":invoices.to_csv(index=False).encode("utf-8-sig"),"das.csv":pd.DataFrame(das_rows).to_csv(index=False).encode("utf-8-sig"),"contatos.csv":pd.DataFrame(contacts).to_csv(index=False).encode("utf-8-sig"),"obrigacoes.csv":pd.DataFrame(obligations).to_csv(index=False).encode("utf-8-sig")}
    for name,data in files.items(): st.download_button(f"Baixar {name}",data,name,"text/csv",use_container_width=True)


st.divider()
st.caption("Razync Pro • Ecossistema Razync • ferramenta de organização contábil e financeira para MEI")
