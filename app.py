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
    update_obligation_status, upsert_das,
)
from fiscal_rules import (
    MEI_ANNUAL_LIMIT, annual_limit_for, build_alerts, competence_list,
    das_due_date, das_status,
)
from reports import dasn_summary_pdf, monthly_report_pdf, financial_summary_pdf, closing_summary_pdf
from bank_import import read_statement, prepare_statement, is_probable_duplicate, suggest_category
from mei_obligations import automatic_obligations
from business_tools import monthly_closing, financial_analysis, consistency_checks
from product_core import NAV_GROUPS, group_for_page, action_items, reconciliation_summary, assistant_answer

CURRENT_YEAR = date.today().year

st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
:root{--rz-blue:#2563eb;--rz-blue2:#60a5fa;--rz-bg:#050914;--rz-card:#0b1220;--rz-border:#1f2a3d}
.stApp{background:radial-gradient(circle at 12% 0%,#0b1832 0%,#050914 36%,#050914 100%)}
[data-testid="stSidebar"]{background:#070c16;border-right:1px solid #172236}
.block-container{padding-top:1.05rem;padding-bottom:2rem;max-width:1500px}
[data-testid="stMetric"]{background:linear-gradient(180deg,rgba(17,28,49,.97),rgba(9,16,29,.97));border:1px solid #1d2a42;border-radius:15px;padding:14px 16px}
.rz-brand{font-size:1.55rem;font-weight:900;letter-spacing:-.04em}.rz-brand span{color:#60a5fa}
.rz-kicker{color:#60a5fa;font-weight:800;text-transform:uppercase;letter-spacing:.14em;font-size:.72rem}
.rz-title{font-size:2rem;font-weight:900;margin:.15rem 0 .18rem;letter-spacing:-.035em}
.rz-sub{color:#94a3b8;margin-bottom:1rem}
.rz-alert{border-radius:13px;padding:11px 13px;margin-bottom:8px;background:#0b1425;border:1px solid #1f2d45}
.rz-ok{border-left:4px solid #22c55e}.rz-info{border-left:4px solid #3b82f6}.rz-warn{border-left:4px solid #f59e0b}.rz-danger{border-left:4px solid #ef4444}
.rz-small{color:#94a3b8;font-size:.86rem}
div[data-testid="stButton"] button,div[data-testid="stFormSubmitButton"] button{border-radius:10px}
div[data-testid="stDataFrame"]{border:1px solid #1c2940;border-radius:12px;overflow:hidden}
</style>
""", unsafe_allow_html=True)


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def header(title: str, subtitle: str) -> None:
    st.markdown('<div class="rz-kicker">Razync Pro • MEI</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-sub">{subtitle}</div>', unsafe_allow_html=True)


def alert_box(level: str, title: str, text: str) -> None:
    cls = {"ok":"rz-ok","info":"rz-info","warn":"rz-warn","danger":"rz-danger"}.get(level, "rz-info")
    st.markdown(f'<div class="rz-alert {cls}"><b>{title}</b><div class="rz-small">{text}</div></div>', unsafe_allow_html=True)


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
    target_group = group_for_page(pending_page)
    st.session_state["nav_group"] = target_group
    st.session_state[f"nav_page_{target_group}"] = pending_page

with st.sidebar:
    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)
    st.caption("Ecossistema Razync • Gestão completa do MEI")
    st.divider()
    groups = list(NAV_GROUPS.keys())
    if st.session_state.get("nav_group") not in groups:
        st.session_state["nav_group"] = "Visão Geral"
    selected_group = st.selectbox("Área", groups, key="nav_group")
    group_pages = NAV_GROUPS[selected_group]
    page_key = f"nav_page_{selected_group}"
    if st.session_state.get(page_key) not in group_pages:
        st.session_state[page_key] = group_pages[0]
    page = st.radio("Navegação", group_pages, label_visibility="collapsed", key=page_key)
    st.divider()
    st.caption("Modo de desenvolvimento • acesso direto")

opening = opening_date_from(profile)
limit = annual_limit_for(opening, CURRENT_YEAR, profile.get("annual_limit"))
year_tx = transactions[(transactions["tx_date"].dt.year==CURRENT_YEAR)] if not transactions.empty else transactions
year_revenue = float(year_tx[year_tx["tx_type"]=="Receita"]["value"].sum()) if not year_tx.empty else 0.0
year_expense = float(year_tx[year_tx["tx_type"]=="Despesa"]["value"].sum()) if not year_tx.empty else 0.0
limit_pct = (year_revenue/limit*100) if limit else 0.0

if page == "Dashboard":
    header("Visão geral","Uma central contábil e financeira para acompanhar o seu MEI.")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Receita no ano",brl(year_revenue)); c2.metric("Despesas no ano",brl(year_expense)); c3.metric("Resultado estimado",brl(year_revenue-year_expense)); c4.metric("Limite utilizado",f"{limit_pct:.1f}%"); c5.metric("Documentos",len(docs))

    st.subheader("Prioridades de hoje")
    priorities = action_items(profile, transactions, invoices, das_rows, obligations, limit, year_revenue)
    for idx, item in enumerate(priorities[:4]):
        a,b = st.columns([5,1])
        with a:
            level = "danger" if item["priority"] == 1 else "warn" if item["priority"] == 2 else "info" if item["priority"] == 3 else "ok"
            alert_box(level, item["title"], item["detail"])
        with b:
            if item["page"] != "Dashboard" and st.button("Resolver", key=f"priority_{idx}", use_container_width=True):
                st.session_state["_navigate_to"] = item["page"]
                st.rerun()

    st.caption("Ações rápidas")
    q1,q2,q3,q4 = st.columns(4)
    if q1.button("+ Lançamento", use_container_width=True): st.session_state["_navigate_to"]="Movimentações"; st.rerun()
    if q2.button("Importar extrato", use_container_width=True): st.session_state["_navigate_to"]="Importar Extrato"; st.rerun()
    if q3.button("Ver DAS", use_container_width=True): st.session_state["_navigate_to"]="DAS"; st.rerun()
    if q4.button("Obrigações", use_container_width=True): st.session_state["_navigate_to"]="Obrigações"; st.rerun()
    left,right = st.columns([1.55,1])
    with left:
        st.subheader("Faturamento por mês")
        chart = pd.DataFrame(monthly_rows(transactions,CURRENT_YEAR))
        fig = px.bar(chart,x="month_name",y="total")
        fig.update_layout(height=330,margin=dict(l=0,r=0,t=8,b=0),xaxis_title="",yaxis_title="Receita")
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.subheader("O que precisa de atenção")
        for level,title,text in build_alerts(year_revenue,limit,das_rows,obligations,profile):
            alert_box(level,title,text)
    st.subheader("Últimos lançamentos")
    if transactions.empty:
        st.info("Cadastre sua primeira movimentação.")
    else:
        st.dataframe(transactions.head(10)[["tx_date","tx_type","description","counterparty","value"]],use_container_width=True,hide_index=True,column_config={"tx_date":st.column_config.DateColumn("Data",format="DD/MM/YYYY"),"value":st.column_config.NumberColumn("Valor",format="R$ %.2f")})

    st.subheader("Saúde do seu MEI")
    health_score, health_notes = mei_health_score(profile, year_revenue, limit, das_rows, obligations)
    a,b = st.columns([1,2])
    with a:
        st.metric("Índice de organização", f"{health_score}/100")
        st.progress(health_score/100)
    with b:
        if health_notes:
            for note in health_notes:
                st.caption(f"• {note}")
        else:
            st.success("Seu cadastro e obrigações monitoradas estão organizados.")

    with st.expander("Checklist de configuração do MEI", expanded=not bool(profile.get("cnpj"))):
        checklist = [
            ("Dados do CNPJ preenchidos", bool(profile.get("cnpj"))),
            ("Atividade principal informada", bool(profile.get("main_activity"))),
            ("Data de abertura cadastrada", bool(profile.get("opening_date"))),
            ("Primeira movimentação registrada", not transactions.empty),
            ("Calendário do DAS criado", bool(das_rows)),
            ("Primeiro documento armazenado", bool(docs)),
        ]
        for label, done in checklist:
            st.write(("✅ " if done else "⬜ ") + label)

elif page == "Movimentações":
    header("Movimentações","Registre receitas e despesas. Os dados alimentam automaticamente o dashboard, o Relatório Mensal e a DASN-SIMEI.")
    with st.form("tx_form",clear_on_submit=True):
        a,b,c = st.columns(3); tx_type = a.selectbox("Tipo",["Receita","Despesa"]); tx_date = b.date_input("Data",date.today()); value = c.number_input("Valor",min_value=0.0,step=10.0)
        desc = st.text_input("Descrição")
        a,b,c = st.columns(3); category = a.selectbox("Categoria",["Serviços","Vendas","Fornecedores","Aluguel","Transporte","Marketing","Impostos","Folha","Outras"]); counterparty = b.text_input("Cliente/fornecedor"); payment_method = c.selectbox("Forma de pagamento",["PIX","Dinheiro","Cartão","Boleto","Transferência","Outro"])
        document_number = st.text_input("Número da nota/documento (opcional)")
        if st.form_submit_button("Salvar lançamento",type="primary",use_container_width=True):
            if not desc.strip() or value <= 0: st.error("Informe descrição e valor maior que zero.")
            else:
                add_transaction(uid,tx_date=tx_date,tx_type=tx_type,description=desc.strip(),category=category,value=float(value),document_number=document_number.strip(),counterparty=counterparty.strip(),payment_method=payment_method); st.rerun()
    if transactions.empty: st.info("Nenhum lançamento.")
    else:
        st.dataframe(transactions[["id","tx_date","tx_type","description","category","document_number","counterparty","payment_method","value"]],use_container_width=True,hide_index=True)
        with st.expander("Excluir lançamento"):
            selected = st.selectbox("ID do lançamento",transactions["id"].tolist())
            if st.button("Excluir definitivamente"): delete_transaction(uid,int(selected)); st.rerun()

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
    header("Conciliação","Confira notas, receitas e possíveis duplicidades antes do fechamento mensal.")
    rec = reconciliation_summary(transactions, invoices)
    c1,c2,c3 = st.columns(3)
    c1.metric("Notas emitidas", rec["total_invoices"])
    c2.metric("Notas conciliadas", rec["reconciled_invoices"])
    c3.metric("Possíveis duplicidades", rec["possible_duplicate_transactions"])
    pending_inv = rec["pending_invoices"]
    st.subheader("Notas pendentes de conciliação")
    if pending_inv.empty:
        st.success("Todas as notas com número informado estão conciliadas com receitas cadastradas.")
    else:
        st.dataframe(pending_inv, use_container_width=True, hide_index=True, column_config={"Valor":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        selected_invoice = st.selectbox("Conciliar nota", pending_inv["ID"].tolist(), key="rec_invoice")
        source = invoices[invoices["id"] == selected_invoice].iloc[0]
        if st.button("Criar receita a partir desta nota", type="primary", use_container_width=True):
            issue = source["issue_date"]
            tx_date_value = issue.date() if hasattr(issue, "date") else issue
            add_transaction(uid, tx_date=tx_date_value, tx_type="Receita", description=source.get("description") or f"Nota {source.get('number') or ''}", category="Serviços" if source.get("invoice_type") == "Serviço" else "Vendas", value=float(source.get("amount") or 0), document_number=str(source.get("number") or ""), counterparty=str(source.get("customer") or ""), payment_method="Outro")
            st.success("Receita criada e nota conciliada.")
            st.rerun()
    st.subheader("Validações")
    checks = pd.DataFrame(consistency_checks(transactions, invoices, das_rows))
    st.dataframe(checks, use_container_width=True, hide_index=True)
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
    fig.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), xaxis_title="", yaxis_title="Valor")
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.line(flow, x="Mês", y="Saldo acumulado", markers=True)
    fig2.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), xaxis_title="", yaxis_title="Saldo acumulado")
    st.plotly_chart(fig2, use_container_width=True)
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
            fig.update_layout(height=340, margin=dict(l=0,r=0,t=8,b=0), xaxis_title="Mês", yaxis_title="Valor")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        exp = analysis["expense_categories"]
        if exp.empty:
            st.info("Ainda não existem despesas no período.")
        else:
            fig = px.pie(exp, names="Categoria", values="Valor", hole=.45)
            fig.update_layout(height=340, margin=dict(l=0,r=0,t=8,b=0))
            st.plotly_chart(fig, use_container_width=True)
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
    header("Notas Fiscais","Controle as notas e concilie cada emissão com o faturamento.")
    with st.form("invoice_form",clear_on_submit=True):
        a,b,c = st.columns(3); issue_date = a.date_input("Data de emissão",date.today()); invoice_type = b.selectbox("Tipo",["Serviço","Mercadoria"]); number = c.text_input("Número")
        customer = st.text_input("Cliente"); a,b = st.columns(2); customer_document = a.text_input("CPF/CNPJ do cliente"); amount = b.number_input("Valor",min_value=0.0); description = st.text_input("Descrição"); status = st.selectbox("Situação",["Emitida","Cancelada","Substituída"])
        if st.form_submit_button("Registrar nota",type="primary",use_container_width=True):
            if amount <= 0 or not customer.strip(): st.error("Informe cliente e valor.")
            else: add_invoice(uid,issue_date=issue_date,invoice_type=invoice_type,number=number.strip(),customer=customer.strip(),customer_document=customer_document.strip(),description=description.strip(),amount=float(amount),status=status); st.rerun()
    st.link_button("Abrir Emissor Nacional de NFS-e","https://www.nfse.gov.br/EmissorNacional",use_container_width=True)
    if invoices.empty: st.info("Nenhuma nota registrada.")
    else:
        st.dataframe(invoices[["id","issue_date","invoice_type","number","customer","amount","status"]],use_container_width=True,hide_index=True)
        active = invoices[invoices["status"]=="Emitida"]; documented = set(transactions["document_number"].fillna("").astype(str)) if not transactions.empty else set(); unreconciled = active[~active["number"].fillna("").astype(str).isin(documented)]
        if not unreconciled.empty:
            st.warning(f"{len(unreconciled)} nota(s) emitida(s) ainda não aparecem vinculadas a uma receita pelo número do documento.")
            selected = st.selectbox("Criar receita a partir da nota",unreconciled["id"].tolist()); row = unreconciled[unreconciled["id"]==selected].iloc[0]
            if st.button("Conciliar nota como receita",type="primary"):
                add_transaction(uid,tx_date=row["issue_date"].date(),tx_type="Receita",description=row["description"] or f"Nota {row['number']}",category="Serviços" if row["invoice_type"]=="Serviço" else "Vendas",value=float(row["amount"]),document_number=str(row["number"] or ""),counterparty=str(row["customer"] or ""),payment_method="Outro"); st.rerun()
        with st.expander("Excluir registro de nota"):
            iid = st.selectbox("ID da nota",invoices["id"].tolist())
            if st.button("Excluir nota do controle"): delete_invoice(uid,int(iid)); st.rerun()

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
    if odf.empty: st.info("Nenhuma obrigação cadastrada.")
    else:
        st.dataframe(odf,use_container_width=True,hide_index=True); a,b=st.columns(2); oid=a.selectbox("ID",odf["id"].tolist()); new_status=b.selectbox("Status",["Pendente","Concluído"]); c,d=st.columns(2)
        if c.button("Atualizar status",use_container_width=True): update_obligation_status(uid,int(oid),new_status); st.rerun()
        if d.button("Excluir obrigação",use_container_width=True): delete_obligation(uid,int(oid)); st.rerun()

elif page == "Clientes e Fornecedores":
    header("Clientes e Fornecedores","Organize os contatos usados nas vendas, compras e documentos.")
    with st.form("contact_form",clear_on_submit=True):
        a,b=st.columns(2); ctype=a.selectbox("Tipo",["Cliente","Fornecedor"]); name=b.text_input("Nome"); a,b,c=st.columns(3); document=a.text_input("CPF/CNPJ"); email=b.text_input("E-mail"); phone=c.text_input("Telefone"); notes=st.text_input("Observações")
        if st.form_submit_button("Salvar contato",type="primary") and name.strip(): add_contact(uid,contact_type=ctype,name=name.strip(),document=document,email=email,phone=phone,notes=notes); st.rerun()
    cdf=pd.DataFrame(list_contacts(uid))
    if cdf.empty: st.info("Nenhum contato.")
    else:
        st.dataframe(cdf,use_container_width=True,hide_index=True); cid=st.selectbox("Excluir contato por ID",cdf["id"].tolist())
        if st.button("Excluir contato"): delete_contact(uid,int(cid)); st.rerun()

elif page == "Empregado":
    header("Empregado","Controle básico do empregado do MEI e mantenha a informação pronta para conferência anual.")
    with st.form("employee_form",clear_on_submit=True):
        name=st.text_input("Nome"); a,b,c=st.columns(3); cpf=a.text_input("CPF"); admission=b.date_input("Admissão",date.today()); salary=c.number_input("Salário",min_value=0.0); status=st.selectbox("Status",["Ativo","Desligado"]); notes=st.text_input("Observações")
        if st.form_submit_button("Salvar empregado",type="primary") and name.strip(): add_employee(uid,name=name.strip(),cpf=cpf,admission_date=admission,salary=float(salary),status=status,notes=notes); st.rerun()
    edf=pd.DataFrame(list_employees(uid))
    if edf.empty: st.info("Nenhum empregado cadastrado.")
    else:
        st.dataframe(edf,use_container_width=True,hide_index=True); eid=st.selectbox("Excluir empregado por ID",edf["id"].tolist())
        if st.button("Excluir empregado"): delete_employee(uid,int(eid)); st.rerun()

elif page == "Documentos":
    header("Documentos","Cofre de notas, recibos, comprovantes, DAS e outros documentos do MEI.")
    with st.form("doc_form",clear_on_submit=True):
        category=st.selectbox("Categoria",["Nota fiscal","Recibo","Comprovante","DAS","DASN-SIMEI","Contrato","Extrato","Outro"]); reference_month=st.text_input("Mês de referência",placeholder="AAAA-MM"); uploaded=st.file_uploader("Arquivo",type=["pdf","png","jpg","jpeg","xlsx","csv"])
        if st.form_submit_button("Salvar documento",type="primary"):
            if uploaded is None: st.error("Selecione um arquivo.")
            else: save_document(uid,uploaded.name,uploaded.type or "",uploaded.getvalue(),category,reference_month.strip()); st.rerun()
    ddf=pd.DataFrame(list_documents(uid))
    if ddf.empty: st.info("Nenhum documento salvo.")
    else:
        st.dataframe(ddf,use_container_width=True,hide_index=True); did=st.selectbox("Documento",ddf["id"].tolist()); doc=get_document(uid,int(did))
        if doc:
            a,b=st.columns(2); a.download_button("Baixar documento",doc["content"],doc["filename"],doc.get("mime_type") or "application/octet-stream",use_container_width=True)
            if b.button("Excluir documento",use_container_width=True): delete_document(uid,int(did)); st.rerun()

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

elif page == "Meu MEI":
    header("Meu MEI","Dados usados nos cálculos, relatórios e alertas do Razync Pro.")
    with st.form("profile_form"):
        a,b=st.columns(2); business_name=a.text_input("Nome empresarial",value=str(profile.get("business_name") or "")); trade_name=b.text_input("Nome fantasia",value=str(profile.get("trade_name") or "")); a,b=st.columns(2); cnpj=a.text_input("CNPJ",value=str(profile.get("cnpj") or "")); main_activity=b.text_input("Atividade principal",value=str(profile.get("main_activity") or ""))
        a,b,c=st.columns(3); options=["Serviços","Comércio","Indústria","Misto"]; current=profile.get("activity_type","Serviços"); activity_type=a.selectbox("Tipo principal",options,index=options.index(current) if current in options else 0); opening_date=b.date_input("Data de abertura",value=opening or date.today()); annual_limit=c.number_input("Limite anual de referência",min_value=0.0,value=float(profile.get("annual_limit") or MEI_ANNUAL_LIMIT),step=1000.0)
        a,b,c=st.columns(3); phone=a.text_input("Telefone",value=str(profile.get("phone") or "")); city=b.text_input("Cidade",value=str(profile.get("city") or "")); state=c.text_input("UF",value=str(profile.get("state") or ""),max_chars=2); a,b=st.columns(2); municipal_registration=a.text_input("Inscrição municipal",value=str(profile.get("municipal_registration") or "")); state_registration=b.text_input("Inscrição estadual",value=str(profile.get("state_registration") or ""))
        if st.form_submit_button("Salvar dados",type="primary",use_container_width=True): save_profile(uid,business_name=business_name,trade_name=trade_name,cnpj=cnpj,main_activity=main_activity,activity_type=activity_type,opening_date=opening_date,annual_limit=float(annual_limit),phone=phone,city=city,state=state.upper(),municipal_registration=municipal_registration,state_registration=state_registration); st.rerun()
    st.info(f"Limite monitorado para {CURRENT_YEAR}: {brl(annual_limit_for(opening,CURRENT_YEAR,profile.get('annual_limit')))}.")
    st.caption(f"Referência automática do próximo ano: {brl(annual_limit_for(opening,CURRENT_YEAR+1,profile.get('annual_limit')))}. Regras ficam centralizadas no módulo fiscal para atualização anual.")

elif page == "Backup":
    header("Backup e exportação","Baixe uma cópia dos principais dados cadastrados.")
    files={"movimentacoes.csv":transactions.to_csv(index=False).encode("utf-8-sig"),"notas_fiscais.csv":invoices.to_csv(index=False).encode("utf-8-sig"),"das.csv":pd.DataFrame(das_rows).to_csv(index=False).encode("utf-8-sig"),"contatos.csv":pd.DataFrame(contacts).to_csv(index=False).encode("utf-8-sig"),"obrigacoes.csv":pd.DataFrame(obligations).to_csv(index=False).encode("utf-8-sig")}
    for name,data in files.items(): st.download_button(f"Baixar {name}",data,name,"text/csv",use_container_width=True)

st.divider()
st.caption("Razync Pro • Ecossistema Razync • ferramenta de organização contábil e financeira para MEI")
