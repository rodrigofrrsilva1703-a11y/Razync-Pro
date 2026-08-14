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
    dashboard_financial_summary, transaction_document_numbers, count_transactions, list_transactions_page,
    load_user_snapshot, data_version, DatabaseConnectionError, resolve_supabase_user,
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
from login_security import login_attempt_guard
from storage_service import download_document, remove_document, upload_document
from auth_service import (
    AuthServiceError, is_supabase_auth_configured, reset_password,
    sign_in as supabase_sign_in, sign_out as supabase_sign_out,
    sign_up as supabase_sign_up,
)

CURRENT_YEAR = date.today().year

st.set_page_config(page_title="Razync Pro", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")
try:
    init_db()
except DatabaseConnectionError as exc:
    st.error("Não foi possível conectar o Razync Pro ao banco definitivo.")
    st.warning(str(exc))
    st.markdown("**Confira os Secrets do Streamlit:**")
    st.code('SUPABASE_DB_PASSWORD = "sua senha"\nSUPABASE_DB_HOST = "aws-0-sa-east-1.pooler.supabase.com"\nSUPABASE_DB_USER = "postgres.etimfgenlludorrftapb"\nSUPABASE_DB_PORT = "5432"', language="toml")
    st.caption("A senha nunca é exibida pelo diagnóstico. Depois de corrigir os Secrets, salve e faça Reboot app.")
    st.stop()

if "ui_theme" not in st.session_state:
    st.session_state["ui_theme"] = "Claro"

UI_THEME = st.session_state["ui_theme"]
PLOT_TEMPLATE = tokens(UI_THEME)["plot"]
inject_design_system(UI_THEME)


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def header(title: str, subtitle: str) -> None:
    page_header(title, subtitle)


def alert_box(level: str, title: str, text: str) -> None:
    alert_card(level, title, text)


def document_bytes(document: dict) -> bytes:
    if document.get("storage_path"):
        return download_document(
            st.session_state.get("access_token", ""),
            st.session_state.get("refresh_token", ""),
            document["storage_path"],
        )
    return document.get("content") or b""


def save_uploaded_document(
    user: dict, uploaded, category: str, reference_month: str
) -> None:
    if user.get("auth_user_id") and st.session_state.get("access_token"):
        storage_path = upload_document(
            user["auth_user_id"],
            st.session_state["access_token"],
            st.session_state["refresh_token"],
            uploaded.name,
            uploaded.getvalue(),
            uploaded.type,
        )
        save_document(
            int(user["id"]), uploaded.name, uploaded.type, None,
            category, reference_month, storage_path=storage_path,
        )
    else:
        save_document(
            int(user["id"]), uploaded.name, uploaded.type, uploaded.getvalue(),
            category, reference_month,
        )


def remove_saved_document(user_id: int, document: dict) -> None:
    if document.get("storage_path"):
        remove_document(
            st.session_state.get("access_token", ""),
            st.session_state.get("refresh_token", ""),
            document["storage_path"],
        )
    delete_document(user_id, int(document["id"]))


def ensure_login() -> dict:
    """Require an authenticated session before loading any business data."""
    auth_enabled = is_supabase_auth_configured()

    if "user" in st.session_state:
        user = st.session_state["user"]
        with st.sidebar:
            st.caption(f"Conectado como {user['name']}")
            if st.button("Sair", use_container_width=True):
                if auth_enabled:
                    supabase_sign_out(
                        st.session_state.get("access_token", ""),
                        st.session_state.get("refresh_token", ""),
                    )
                for key in list(st.session_state):
                    del st.session_state[key]
                st.rerun()
        return user

    st.markdown(
        """
        <div class="rz-login-shell">
          <div class="rz-login-brand">
            <div class="rz-login-mark" aria-hidden="true"></div>
            <div><strong>Razync</strong><span>PRO</span></div>
          </div>
          <div class="rz-login-kicker">Gestão inteligente para MEI</div>
          <h1>Seu negócio organizado.<br><em>Suas decisões mais simples.</em></h1>
          <p class="rz-login-lead">Finanças, obrigações fiscais e documentos em um só lugar, com segurança e clareza para você focar no crescimento.</p>
          <div class="rz-login-benefits">
            <span>✓ Controle financeiro</span>
            <span>✓ Rotina fiscal</span>
            <span>✓ Documentos protegidos</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not auth_enabled:
        st.warning(
            "Supabase Auth ainda não está configurado neste ambiente. "
            "O acesso temporário de migração está ativo."
        )

    login_tab, signup_tab, recovery_tab = st.tabs(
        ["Entrar", "Criar conta", "Recuperar senha"]
    )

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("E-mail", key="login_email").strip()
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Informe o e-mail e a senha.")
            else:
                retry_after = login_attempt_guard.retry_after(email)
                if retry_after:
                    minutes = max(1, (retry_after + 59) // 60)
                    st.error(f"Muitas tentativas. Tente novamente em {minutes} minuto(s).")
                else:
                    try:
                        if auth_enabled:
                            identity = supabase_sign_in(email, password)
                            user = resolve_supabase_user(
                                identity["auth_user_id"],
                                identity["email"],
                                identity.get("name", ""),
                            )
                            st.session_state["access_token"] = identity["access_token"]
                            st.session_state["refresh_token"] = identity["refresh_token"]
                        else:
                            user = authenticate(email, password)
                    except (AuthServiceError, DatabaseConnectionError, ValueError) as exc:
                        user = None
                        if isinstance(exc, DatabaseConnectionError):
                            st.error("Não foi possível acessar sua conta agora.")
                            st.warning(str(exc))

                    if user:
                        login_attempt_guard.record_success(email)
                        st.session_state["user"] = user
                        st.rerun()

                    retry_after = login_attempt_guard.record_failure(email)
                    if retry_after:
                        minutes = max(1, (retry_after + 59) // 60)
                        st.error(f"Muitas tentativas. Tente novamente em {minutes} minuto(s).")
                    else:
                        st.error("E-mail ou senha inválidos, ou e-mail ainda não confirmado.")

    with signup_tab:
        with st.form("signup_form"):
            name = st.text_input("Nome", key="signup_name").strip()
            email = st.text_input("E-mail", key="signup_email").strip()
            password = st.text_input(
                "Senha", type="password", key="signup_password",
                help="Use pelo menos 8 caracteres.",
            )
            confirmation = st.text_input(
                "Confirmar senha", type="password",
                key="signup_password_confirmation",
            )
            submitted = st.form_submit_button("Criar conta", use_container_width=True)

        if submitted:
            if password != confirmation:
                st.error("As senhas não coincidem.")
            elif auth_enabled:
                try:
                    identity = supabase_sign_up(name, email, password)
                    if identity["confirmed"]:
                        user = resolve_supabase_user(
                            identity["auth_user_id"], identity["email"], identity["name"]
                        )
                        st.session_state["access_token"] = identity["access_token"]
                        st.session_state["refresh_token"] = identity["refresh_token"]
                        st.session_state["user"] = user
                        st.rerun()
                    st.success("Conta criada. Confirme o e-mail antes de entrar.")
                except (AuthServiceError, DatabaseConnectionError, ValueError) as exc:
                    st.error(str(exc))
            else:
                try:
                    created, message = create_user(name, email, password)
                except DatabaseConnectionError as exc:
                    st.error("Não foi possível criar sua conta agora.")
                    st.warning(str(exc))
                else:
                    if created:
                        user = authenticate(email, password)
                        if user:
                            st.session_state["user"] = user
                            st.success(message)
                            st.rerun()
                    else:
                        st.error(message)

    with recovery_tab:
        if auth_enabled:
            with st.form("password_recovery_form"):
                email = st.text_input("E-mail", key="recovery_email").strip()
                submitted = st.form_submit_button(
                    "Enviar recuperação", use_container_width=True
                )
            if submitted:
                try:
                    reset_password(email)
                    st.success(
                        "Se existir uma conta com este e-mail, enviaremos as instruções."
                    )
                except AuthServiceError as exc:
                    st.error(str(exc))
        else:
            st.info("A recuperação estará disponível após configurar o Supabase Auth.")

    st.stop()


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

pending_page = st.session_state.pop("_navigate_to", None)
if pending_page:
    st.session_state["_current_page"] = pending_page

page = st.session_state.get("_current_page", "Dashboard")
all_pages = [p for pages in NAV_GROUPS.values() for p in pages]
if page not in all_pages:
    page = "Dashboard"
    st.session_state["_current_page"] = page

# PERFORMANCE V15: one Supabase round-trip per session/data change.
_snapshot_key = f"_mei_snapshot_{uid}"
_snapshot_version_key = f"_mei_snapshot_version_{uid}"
_current_data_version = data_version(uid)
if _snapshot_key not in st.session_state or st.session_state.get(_snapshot_version_key) != _current_data_version:
    try:
        st.session_state[_snapshot_key] = load_user_snapshot(uid)
        st.session_state[_snapshot_version_key] = _current_data_version
    except DatabaseConnectionError as exc:
        st.error("Não foi possível sincronizar os dados do Razync Pro.")
        st.warning(str(exc))
        st.stop()

_snapshot = st.session_state[_snapshot_key]
profile = dict(_snapshot.get("profile") or {})

transactions = pd.DataFrame(_snapshot.get("transactions") or [])
if transactions.empty:
    transactions = pd.DataFrame(columns=["id","tx_date","tx_type","description","category","value","document_number","counterparty","payment_method"])
else:
    transactions["tx_date"] = pd.to_datetime(transactions["tx_date"])

invoices = pd.DataFrame(_snapshot.get("invoices") or [])
if not invoices.empty:
    invoices["issue_date"] = pd.to_datetime(invoices["issue_date"])

das_rows = list(_snapshot.get("das") or [])
docs = list(_snapshot.get("documents") or [])
employees = list(_snapshot.get("employees") or [])
contacts = list(_snapshot.get("contacts") or [])
obligations = list(_snapshot.get("obligations") or [])

# Shared financial context used by Dashboard and fiscal/management pages.
opening = opening_date_from(profile)
limit = annual_limit_for(opening, CURRENT_YEAR, profile.get("annual_limit"))
year_tx = transactions[(transactions["tx_date"].dt.year == CURRENT_YEAR)] if not transactions.empty else transactions
year_revenue = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
year_expense = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0
limit_pct = (year_revenue / limit * 100.0) if limit else 0.0

# Pagination context for the transaction history. Keep it local to the in-memory snapshot.
page_size = 50
total_tx = len(transactions)
current_tx_page = int(st.session_state.get("tx_history_page", 1))
max_tx_page = max(1, (total_tx + page_size - 1) // page_size)
current_tx_page = min(max(current_tx_page, 1), max_tx_page)
if page == "Movimentações" and not transactions.empty:
    offset = (current_tx_page - 1) * page_size
    transactions = transactions.iloc[offset:offset + page_size].copy()

with st.sidebar:
    st.markdown("### RAZYNC PRO")
    st.caption("Contabilidade simples para MEI")
    st.selectbox("Tema", ["Claro", "Escuro"], key="ui_theme")
    st.markdown("**Navegação**")
    if page == "Dashboard":
        st.info("⌂ Início")
    elif st.button("⌂ Início", key="nav_home", use_container_width=True):
        st.session_state["_navigate_to"] = "Dashboard"
        st.rerun()
    groups = {
        "Financeiro": NAV_GROUPS["Financeiro"],
        "Fiscal MEI": NAV_GROUPS["Fiscal MEI"],
        "Gestão": NAV_GROUPS["Gestão"],
        "Relatórios": NAV_GROUPS["Relatórios"],
        "Configurações": NAV_GROUPS["Configurações"],
    }
    for group, pages in groups.items():
        with st.expander(group, expanded=(group_for_page(page) == group)):
            for nav_page in pages:
                if nav_page == page:
                    st.info(nav_page)
                elif st.button(nav_page, key=f"nav_{group}_{nav_page}", use_container_width=True):
                    st.session_state["_navigate_to"] = nav_page
                    st.rerun()

# Dashboard metrics are calculated from the local snapshot — zero network calls while navigating.
_dashboard_stats = None
if page == "Dashboard":
    business_label = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"
    cnpj_label = str(profile.get("cnpj") or "").strip() or None
    page_header("Visão geral", "Seu financeiro e suas obrigações em uma tela, com foco no que precisa de ação agora.")
    business_card(business_label, CURRENT_YEAR, cnpj_label)

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
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
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
    header("Movimentações","Registre o que entrou e saiu do MEI. Comece pelo essencial; os detalhes ficam opcionais.")
    with st.container(border=True):
        st.caption("NOVO LANÇAMENTO")
        with st.form("tx_form", clear_on_submit=True):
            tx_type = st.segmented_control("Tipo", ["Receita","Despesa"], default="Receita", selection_mode="single") or "Receita"
            a,b = st.columns(2)
            value = a.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
            tx_date = b.date_input("Data", value=date.today())
            desc = st.text_input("Descrição", placeholder="Ex.: pagamento do cliente, compra de material...")
            with st.expander("Mais detalhes (opcional)"):
                a,b = st.columns(2)
                category = a.selectbox("Categoria", ["Serviços","Vendas","Materiais","Aluguel","Transporte","Taxas","Marketing","Pró-labore/Retirada","Outros"])
                counterparty = b.text_input("Cliente ou fornecedor")
                a,b = st.columns(2)
                payment = a.selectbox("Forma de pagamento", ["PIX","Dinheiro","Cartão","Boleto","Transferência","Outro"])
                doc = b.text_input("Nota ou documento")
            submitted = st.form_submit_button("Salvar movimentação", type="primary", use_container_width=True)
            if submitted:
                if value <= 0:
                    st.error("Informe um valor maior que zero.")
                elif not desc.strip():
                    st.error("Informe uma descrição para identificar o lançamento.")
                else:
                    add_transaction(uid, tx_date=tx_date, tx_type=tx_type, description=desc.strip(), category=category, value=value, document_number=doc.strip(), counterparty=counterparty.strip(), payment_method=payment)
                    st.rerun()
    section("Histórico")
    if transactions.empty:
        empty_state("Nenhuma movimentação registrada", "Quando você adicionar a primeira receita ou despesa, ela aparecerá aqui e alimentará automaticamente o Dashboard e os relatórios.", "↕")
    else:
        view = transactions.copy()
        view["Data"] = view["tx_date"].dt.date; view["Tipo"] = view["tx_type"]; view["Descrição"] = view["description"]; view["Categoria"] = view["category"]; view["Valor"] = view["value"]
        st.dataframe(view[["id","Data","Tipo","Descrição","Categoria","Valor"]], use_container_width=True, hide_index=True, column_config={"id":None,"Valor":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"Data":st.column_config.DateColumn("Data",format="DD/MM/YYYY")})
        if total_tx > page_size:
            pprev, pinfo, pnext = st.columns([1,2,1])
            if pprev.button("← Anterior", disabled=current_tx_page <= 1, use_container_width=True):
                st.session_state["tx_history_page"] = current_tx_page - 1; st.rerun()
            pinfo.caption(f"Página {current_tx_page} de {max_tx_page} • {total_tx} lançamentos")
            if pnext.button("Próxima →", disabled=current_tx_page >= max_tx_page, use_container_width=True):
                st.session_state["tx_history_page"] = current_tx_page + 1; st.rerun()
        with st.expander("Excluir um lançamento"):
            item = st.selectbox("Selecione", transactions["id"].tolist(), format_func=lambda x: f"#{x} - {transactions.loc[transactions['id']==x,'description'].iloc[0]}")
            st.caption("A exclusão é definitiva. Confira o lançamento antes de continuar.")
            if st.button("Excluir lançamento selecionado", use_container_width=True): delete_transaction(uid,int(item)); st.rerun()

elif page == "Importar Extrato":
    header("Importar Extrato","Envie CSV ou Excel. O Razync transforma o extrato em lançamentos para conciliação e relatórios.")
    st.caption("Suporta CSV e XLSX. Na próxima etapa você escolhe quais colunas representam data, descrição e valor.")
    upload = st.file_uploader("Arquivo do extrato", type=["csv","xlsx","xls"], key="statement_file")
    if upload:
        try:
            raw = read_statement(upload, upload.name)
            if raw.empty:
                st.warning("O arquivo não possui linhas para importar.")
            else:
                st.subheader("1. Confira as colunas")
                st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
                cols = list(raw.columns)
                a,b,c = st.columns(3)
                date_col = a.selectbox("Coluna de data", cols, index=0)
                desc_col = b.selectbox("Coluna de descrição", cols, index=min(1,len(cols)-1))
                value_col = c.selectbox("Coluna de valor", cols, index=min(2,len(cols)-1))
                st.subheader("2. Prepare a importação")
                prepared = prepare_statement(raw, date_col, desc_col, value_col)
                prepared["Categoria sugerida"] = prepared["description"].apply(suggest_category)
                if prepared.empty:
                    st.warning("Nenhuma linha válida foi encontrada com esse mapeamento.")
                else:
                    existing_keys = set()
                    if not transactions.empty:
                        existing_keys = set((r.tx_date.date() if hasattr(r.tx_date,"date") else r.tx_date, r.description, float(r.value), r.tx_type) for r in transactions.itertuples())
                    prepared["Duplicado"] = [is_probable_duplicate(existing_keys,row.tx_date,row.description,row.value,row.tx_type) for row in prepared.itertuples()]
                    st.dataframe(prepared, use_container_width=True, hide_index=True, column_config={"value":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"tx_date":st.column_config.DateColumn("Data",format="DD/MM/YYYY")})
                    only_new = st.checkbox("Ignorar possíveis duplicados", value=True)
                    rows_to_import = prepared[~prepared["Duplicado"]] if only_new else prepared
                    st.caption(f"{len(rows_to_import)} lançamento(s) serão importados.")
                    if st.button("Confirmar importação", type="primary", use_container_width=True):
                        count=0
                        for _,r in rows_to_import.iterrows():
                            add_transaction(uid, tx_date=r["tx_date"], tx_type=r["tx_type"], description=r["description"], category=r["Categoria sugerida"], value=float(r["value"]), document_number="", counterparty="", payment_method="Banco")
                            count+=1
                        st.success(f"{count} lançamento(s) importados.")
                        st.session_state["_navigate_to"] = "Movimentações"
                        st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível ler o arquivo: {exc}")

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
    header("Fluxo de Caixa","Veja entradas, saídas, resultado e saldo acumulado por mês.")
    year = st.selectbox("Ano",list(range(CURRENT_YEAR-3,CURRENT_YEAR+1)),index=3)
    cf = cashflow_monthly(transactions,year)
    c1,c2,c3 = st.columns(3)
    c1.metric("Entradas",brl(float(cf["Entradas"].sum()))); c2.metric("Saídas",brl(float(cf["Saídas"].sum()))); c3.metric("Resultado",brl(float(cf["Resultado"].sum())))
    fig = px.bar(cf,x="Mês",y=["Entradas","Saídas"],barmode="group",template=PLOT_TEMPLATE)
    themed_plotly_chart(fig,use_container_width=True)
    st.dataframe(cf,use_container_width=True,hide_index=True,column_config={"Entradas":st.column_config.NumberColumn(format="R$ %.2f"),"Saídas":st.column_config.NumberColumn(format="R$ %.2f"),"Resultado":st.column_config.NumberColumn(format="R$ %.2f"),"Saldo acumulado":st.column_config.NumberColumn(format="R$ %.2f")})

elif page == "Análise Financeira":
    header("Análise Financeira","Veja evolução, rentabilidade e pontos que merecem revisão antes de tomar decisões.")
    analysis_year = st.selectbox("Ano da análise", list(range(CURRENT_YEAR-3,CURRENT_YEAR+1)), index=3, key="analysis_year")
    analysis = financial_analysis(transactions, analysis_year)
    ac1,ac2,ac3,ac4 = st.columns(4)
    ac1.metric("Receitas",brl(analysis["revenue"])); ac2.metric("Despesas",brl(analysis["expense"])); ac3.metric("Resultado",brl(analysis["result"])); ac4.metric("Margem",f"{analysis['margin']:.1f}%")
    monthly = analysis["monthly"]
    if not monthly.empty:
        fig = px.line(monthly,x="Mês",y=["Receitas","Despesas","Resultado"],markers=True,template=PLOT_TEMPLATE)
        themed_plotly_chart(fig,use_container_width=True)
        st.dataframe(monthly,use_container_width=True,hide_index=True,column_config={c:st.column_config.NumberColumn(format="R$ %.2f") for c in ["Receitas","Despesas","Resultado"]})
    st.subheader("Despesas por categoria")
    bycat = analysis["expense_by_category"]
    if bycat.empty: st.info("Sem despesas registradas neste ano.")
    else:
        fig2=px.bar(bycat,x="Categoria",y="Valor",template=PLOT_TEMPLATE); themed_plotly_chart(fig2,use_container_width=True)
    checks = consistency_checks(transactions,invoices,das_rows)
    st.subheader("Revisões recomendadas")
    if checks:
        for item in checks: st.warning(item)
    else: st.success("Nenhuma inconsistência relevante encontrada.")
    analysis_pdf = financial_summary_pdf(profile, analysis_year, analysis, checks)
    st.download_button("Baixar análise financeira em PDF",analysis_pdf,file_name=f"analise_financeira_{analysis_year}.pdf",mime="application/pdf",use_container_width=True)

elif page == "Central Fiscal":
    header("Central Fiscal MEI","Acompanhe limite, DAS, relatório mensal e DASN em um único lugar.")
    fiscal_year = st.selectbox("Ano fiscal",list(range(CURRENT_YEAR-2,CURRENT_YEAR+1)),index=2,key="fiscal_year")
    f_limit = annual_limit_for(opening,fiscal_year,profile.get("annual_limit"))
    f_tx = transactions[(transactions["tx_date"].dt.year==fiscal_year)] if not transactions.empty else transactions
    f_rev = float(f_tx[f_tx["tx_type"]=="Receita"]["value"].sum()) if not f_tx.empty else 0.0
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Faturamento",brl(f_rev)); c2.metric("Limite monitorado",brl(f_limit)); c3.metric("Disponível",brl(max(f_limit-f_rev,0))); c4.metric("Uso",f"{(f_rev/f_limit*100 if f_limit else 0):.1f}%")
    overdue_das=[d for d in das_rows if das_status(d.get("status","Pendente"),d.get("due_date"))=="Atrasado"]
    pending_das=[d for d in das_rows if das_status(d.get("status","Pendente"),d.get("due_date"))=="Pendente"]
    if overdue_das: st.error(f"{len(overdue_das)} DAS registrado(s) como atrasado(s).")
    elif pending_das: st.info(f"{len(pending_das)} DAS pendente(s) no controle.")
    else: st.success("Nenhum DAS pendente identificado no controle.")
    months=monthly_rows(transactions,fiscal_year)
    year_total=sum(r["total"] for r in months)
    c1,c2,c3=st.columns(3)
    c1.metric("Relatório mensal",f"{sum(1 for r in months if r['total']>0)}/12 meses com movimento")
    c2.metric("Base DASN",brl(year_total))
    c3.metric("Documentos",len(docs))
    q1,q2,q3,q4=st.columns(4)
    if q1.button("Abrir DAS",use_container_width=True): st.session_state["_navigate_to"]="DAS"; st.rerun()
    if q2.button("Relatório Mensal",use_container_width=True): st.session_state["_navigate_to"]="Relatório Mensal"; st.rerun()
    if q3.button("Preparar DASN",use_container_width=True): st.session_state["_navigate_to"]="DASN-SIMEI"; st.rerun()
    if q4.button("Ver Obrigações",use_container_width=True): st.session_state["_navigate_to"]="Obrigações"; st.rerun()

elif page == "Fechamento Mensal":
    header("Fechamento Mensal","Confira documentos, notas, movimentações e DAS antes de considerar o mês organizado.")
    c1,c2=st.columns(2)
    close_year=c1.selectbox("Ano",list(range(CURRENT_YEAR-2,CURRENT_YEAR+1)),index=2,key="close_year")
    close_month=c2.selectbox("Mês",list(range(1,13)),index=date.today().month-1,format_func=lambda m:calendar.month_name[m],key="close_month")
    closing=monthly_closing(transactions,invoices,docs,das_rows,close_year,close_month)
    a,b,c,d=st.columns(4)
    a.metric("Receitas",brl(closing["revenue"])); b.metric("Despesas",brl(closing["expense"])); c.metric("Resultado",brl(closing["result"])); d.metric("Organização",f"{closing['score']}%")
    st.progress(closing["score"]/100)
    for item in closing["checks"]:
        if item["ok"]: st.success(item["text"])
        else: st.warning(item["text"])
    closing_pdf = closing_summary_pdf(profile, close_year, close_month, closing)
    st.download_button("Baixar fechamento em PDF",closing_pdf,file_name=f"fechamento_{close_year}_{close_month:02d}.pdf",mime="application/pdf",use_container_width=True)

elif page == "Relatório Mensal":
    header("Relatório Mensal de Receitas Brutas","Gere o relatório mensal a partir das receitas cadastradas.")
    year=st.selectbox("Ano",list(range(CURRENT_YEAR-3,CURRENT_YEAR+1)),index=3,key="rmyear")
    rows=monthly_rows(transactions,year)
    dfm=pd.DataFrame([{ "Mês":r["month_name"],"Com documento":r["with_doc"],"Sem documento":r["without_doc"],"Serviços":r["services"],"Vendas/Comércio":r["sales"],"Total":r["total"]} for r in rows])
    st.dataframe(dfm,use_container_width=True,hide_index=True,column_config={c:st.column_config.NumberColumn(format="R$ %.2f") for c in ["Com documento","Sem documento","Serviços","Vendas/Comércio","Total"]})
    st.caption("O relatório é gerado com base nos dados cadastrados. Guarde os documentos comprobatórios conforme as regras aplicáveis ao MEI.")
    month=st.selectbox("Mês do PDF",list(range(1,13)),format_func=lambda m:calendar.month_name[m],key="pdfmonth")
    r=rows[month-1]
    pdf=monthly_report_pdf(profile,month,year,r["with_doc"],r["without_doc"],r["services"],r["sales"])
    st.download_button("Baixar relatório em PDF",pdf,file_name=f"relatorio_mensal_{year}_{month:02d}.pdf",mime="application/pdf")

elif page == "Notas Fiscais":
    header("Notas Fiscais","Controle as notas emitidas e acompanhe se cada uma já foi conciliada com uma receita.")
    with st.container(border=True):
        st.caption("NOVA NOTA")
        with st.form("invoice_form",clear_on_submit=True):
            a,b,c=st.columns(3)
            issue=a.date_input("Data de emissão",value=date.today()); inv_type=b.selectbox("Tipo",["Serviço","Venda/Comércio"]); amount=c.number_input("Valor",min_value=0.0,step=10.0,format="%.2f")
            a,b=st.columns(2)
            number=a.text_input("Número da nota"); customer=b.text_input("Cliente",placeholder="Nome do cliente")
            desc=st.text_input("Descrição",placeholder="Ex.: serviço prestado, venda realizada...")
            with st.expander("Mais detalhes (opcional)"):
                custdoc=st.text_input("CPF/CNPJ do cliente")
                status=st.selectbox("Situação",["Emitida","Cancelada"])
            submit=st.form_submit_button("Salvar nota",type="primary",use_container_width=True)
            if submit:
                if amount <= 0: st.error("Informe um valor maior que zero.")
                else:
                    add_invoice(uid,issue_date=issue,invoice_type=inv_type,number=number.strip(),customer=customer.strip(),customer_document=custdoc.strip(),description=desc.strip(),amount=amount,status=status); st.rerun()
    section("Notas cadastradas")
    if invoices.empty:
        empty_state("Nenhuma nota fiscal cadastrada", "Cadastre as notas emitidas para comparar faturamento, acompanhar clientes e facilitar a conciliação com os recebimentos.", "▤")
    else:
        st.dataframe(invoices,use_container_width=True,hide_index=True,column_config={"amount":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"issue_date":st.column_config.DateColumn("Emissão",format="DD/MM/YYYY")})
        with st.expander("Excluir uma nota"):
            iid=st.selectbox("Selecione",invoices["id"].tolist(),key="delinv"); st.caption("Confira antes de excluir: esta ação é definitiva.")
            if st.button("Excluir nota selecionada",use_container_width=True): delete_invoice(uid,int(iid)); st.rerun()

elif page == "DAS":
    header("DAS","Controle as competências mensais e registre pagamentos do Documento de Arrecadação do Simples Nacional.")
    year=st.selectbox("Ano",list(range(CURRENT_YEAR-2,CURRENT_YEAR+1)),index=2,key="dasyear")
    st.caption("O vencimento padrão é calculado para o dia 20 do mês seguinte, com ajuste básico para fim de semana. Consulte sempre o documento oficial antes do pagamento.")
    with st.expander("Registrar ou atualizar uma competência", expanded=not bool(das_rows)):
        month=st.selectbox("Competência",list(range(1,13)),format_func=lambda m:f"{m:02d}/{year}")
        competence=f"{year}-{month:02d}"
        due=st.date_input("Vencimento",value=das_due_date(year,month))
        amount=st.number_input("Valor do DAS",min_value=0.0,step=1.0,format="%.2f")
        status=st.selectbox("Status",["Pendente","Pago"])
        payment_date=None
        if status=="Pago": payment_date=st.date_input("Data de pagamento",value=date.today())
        notes=st.text_area("Observações")
        if st.button("Salvar DAS",type="primary",use_container_width=True): upsert_das(uid,competence,due,amount,status,payment_date,notes); st.rerun()
    current=[d for d in das_rows if str(d["competence"]).startswith(str(year))]
    section("Competências do ano")
    if not current:
        empty_state("Nenhum DAS controlado neste ano", "Adicione uma competência para acompanhar vencimento e pagamento do DAS dentro do Razync.", "▣")
    else:
        das_view=[]
        for d in current:
            das_view.append({"Competência":d["competence"],"Vencimento":d["due_date"],"Valor":d["amount"],"Status":das_status(d["status"],d["due_date"]),"Pagamento":d["payment_date"]})
        st.dataframe(pd.DataFrame(das_view),use_container_width=True,hide_index=True,column_config={"Valor":st.column_config.NumberColumn(format="R$ %.2f"),"Vencimento":st.column_config.DateColumn(format="DD/MM/YYYY"),"Pagamento":st.column_config.DateColumn(format="DD/MM/YYYY")})

elif page == "DASN-SIMEI":
    header("DASN-SIMEI","Prepare os dados anuais para conferir antes da declaração oficial.")
    year=st.selectbox("Ano-calendário",list(range(CURRENT_YEAR-4,CURRENT_YEAR+1)),index=3,key="dasnyear")
    services,sales=category_totals_for_dasn(transactions,year)
    total=services+sales
    c1,c2,c3=st.columns(3); c1.metric("Serviços",brl(services)); c2.metric("Comércio/indústria",brl(sales)); c3.metric("Receita bruta total",brl(total))
    employee=st.checkbox("O MEI teve empregado no ano?",value=bool(profile.get("has_employee",False)))
    pdf=dasn_summary_pdf(profile,year,services,sales,employee)
    st.download_button("Baixar resumo para conferência",pdf,file_name=f"resumo_DASN_{year}.pdf",mime="application/pdf")
    st.warning("O Razync Pro organiza as informações, mas não transmite a DASN-SIMEI ao Portal do Simples Nacional.")

elif page == "Obrigações":
    header("Obrigações","Use o calendário automático do MEI e acrescente tarefas específicas do seu negócio.")
    obligation_year=st.selectbox("Ano",list(range(CURRENT_YEAR-1,CURRENT_YEAR+2)),index=1,key="obyear")
    auto=automatic_obligations(obligation_year,opening)
    manual=obligations
    combined=[]
    for row in auto:
        combined.append({"Origem":"Automática","Obrigação":row["title"],"Tipo":row["category"],"Competência":row["competence"],"Vencimento":row["due_date"],"Status":row["status"],"Detalhes":row["details"]})
    for row in manual:
        combined.append({"Origem":"Manual","Obrigação":row["title"],"Tipo":row["category"],"Competência":"-","Vencimento":row["due_date"],"Status":row["status"],"Detalhes":row["notes"]})
    if combined:
        obd=pd.DataFrame(combined).sort_values("Vencimento")
        st.dataframe(obd,use_container_width=True,hide_index=True,column_config={"Vencimento":st.column_config.DateColumn(format="DD/MM/YYYY")})
    else:
        empty_state("Nenhuma obrigação para exibir", "Quando houver tarefas automáticas ou personalizadas, elas aparecerão aqui organizadas por vencimento.", "✓")
    with st.expander("Adicionar obrigação personalizada"):
        with st.form("obl_form",clear_on_submit=True):
            title=st.text_input("Título"); due=st.date_input("Vencimento",value=date.today()); cat=st.selectbox("Categoria",["Fiscal","Financeira","Administrativa","Trabalhista","Outra"]); notes=st.text_area("Observações")
            if st.form_submit_button("Adicionar",use_container_width=True):
                if title.strip(): add_obligation(uid,title=title.strip(),due_date=due,status="Pendente",category=cat,notes=notes.strip()); st.rerun()
    if manual:
        with st.expander("Atualizar tarefas personalizadas"):
            item=st.selectbox("Tarefa",[o["id"] for o in manual],format_func=lambda x:next(o["title"] for o in manual if o["id"]==x))
            status=st.selectbox("Novo status",["Pendente","Concluído"],key="oblstatus")
            c1,c2=st.columns(2)
            if c1.button("Atualizar",use_container_width=True): update_obligation_status(uid,int(item),status); st.rerun()
            if c2.button("Excluir",use_container_width=True): delete_obligation(uid,int(item)); st.rerun()

elif page == "Clientes e Fornecedores":
    header("Clientes e Fornecedores","Mantenha os contatos essenciais organizados para reutilizar em vendas, compras e documentos.")
    with st.container(border=True):
        st.caption("NOVO CONTATO")
        with st.form("contact_form",clear_on_submit=True):
            a,b=st.columns([1,2]); typ=a.segmented_control("Tipo",["Cliente","Fornecedor"],default="Cliente",selection_mode="single") or "Cliente"; name=b.text_input("Nome",placeholder="Nome ou razão social")
            with st.expander("Mais detalhes (opcional)"):
                a,b,c=st.columns(3); doc=a.text_input("CPF/CNPJ"); email=b.text_input("E-mail"); phone=c.text_input("Telefone")
                notes=st.text_area("Observações")
            save=st.form_submit_button("Salvar contato",type="primary",use_container_width=True)
            if save:
                if not name.strip(): st.error("Informe o nome do contato.")
                else: add_contact(uid,contact_type=typ,name=name.strip(),document=doc.strip(),email=email.strip(),phone=phone.strip(),notes=notes.strip()); st.rerun()
    section("Contatos")
    if not contacts:
        empty_state("Nenhum cliente ou fornecedor", "Adicione seu primeiro contato para organizar quem compra de você e de quem sua empresa compra.", "◇")
    else:
        cdf=pd.DataFrame(contacts); st.dataframe(cdf,use_container_width=True,hide_index=True)
        with st.expander("Excluir contato"):
            cid=st.selectbox("Selecione",[c["id"] for c in contacts],format_func=lambda x:next(c["name"] for c in contacts if c["id"]==x),key="delcontact"); st.caption("A exclusão é definitiva.")
            if st.button("Excluir contato selecionado",use_container_width=True): delete_contact(uid,int(cid)); st.rerun()

elif page == "Empregado":
    header("Empregado","Organize informações básicas quando o MEI possuir empregado registrado.")
    with st.container(border=True):
        st.caption("CADASTRO DO EMPREGADO")
        with st.form("emp_form",clear_on_submit=True):
            name=st.text_input("Nome",placeholder="Nome completo")
            a,b=st.columns(2); admission=a.date_input("Data de admissão",value=date.today()); salary=b.number_input("Salário",min_value=0.0,step=50.0)
            with st.expander("Mais detalhes (opcional)"):
                cpf=st.text_input("CPF"); status=st.selectbox("Status",["Ativo","Inativo"]); notes=st.text_area("Observações")
            save=st.form_submit_button("Salvar empregado",type="primary",use_container_width=True)
            if save:
                if not name.strip(): st.error("Informe o nome do empregado.")
                else: add_employee(uid,name=name.strip(),cpf=cpf.strip(),admission_date=admission,salary=salary,status=status,notes=notes.strip()); st.rerun()
    section("Empregados cadastrados")
    if not employees:
        empty_state("Nenhum empregado cadastrado", "Se o seu MEI possuir empregado, registre os dados básicos aqui para manter essa informação junto da gestão do negócio.", "♙")
    else:
        st.dataframe(pd.DataFrame(employees),use_container_width=True,hide_index=True)
        with st.expander("Excluir empregado"):
            eid=st.selectbox("Selecione",[e["id"] for e in employees],format_func=lambda x:next(e["name"] for e in employees if e["id"]==x),key="delemp"); st.caption("A exclusão é definitiva.")
            if st.button("Excluir empregado selecionado",use_container_width=True): delete_employee(uid,int(eid)); st.rerun()

elif page == "Documentos":
    header("Documentos","Guarde comprovantes, notas e arquivos por competência para encontrar tudo com facilidade no fechamento.")
    with st.container(border=True):
        st.caption("ADICIONAR DOCUMENTO")
        up=st.file_uploader("Escolha um arquivo",key="docup")
        a,b=st.columns(2); category=a.selectbox("Tipo de documento",["Nota Fiscal","Comprovante","Extrato Bancário","DAS","Contrato","Outro"]); reference=b.text_input("Competência",placeholder="AAAA-MM")
        if st.button("Salvar documento",type="primary",use_container_width=True,disabled=up is None):
            if up:
                try:
                    save_uploaded_document(user, up, category, reference.strip())
                except Exception:
                    st.error("Não foi possível armazenar o documento agora.")
                else:
                    st.rerun()
    section("Arquivos salvos")
    if not docs:
        empty_state("Nenhum documento salvo", "Adicione comprovantes, notas e extratos. Eles ficam organizados por tipo e competência para facilitar os fechamentos.", "▱")
    else:
        ddf=pd.DataFrame(docs); st.dataframe(ddf,use_container_width=True,hide_index=True)
        did=st.selectbox("Abrir documento",[d["id"] for d in docs],format_func=lambda x:next(d["filename"] for d in docs if d["id"]==x))
        selected=get_document(uid,int(did))
        if selected:
            try:
                content = document_bytes(selected)
            except Exception:
                st.error("Não foi possível baixar o documento agora.")
            else:
                st.download_button(
                    "Baixar arquivo", content, file_name=selected["filename"],
                    mime=selected["mime_type"] or "application/octet-stream",
                )
        with st.expander("Excluir documento"):
            st.caption("A exclusão remove o arquivo armazenado no Razync.")
            if st.button("Excluir documento selecionado",use_container_width=True):
                try:
                    remove_saved_document(uid, selected)
                except Exception:
                    st.error("Não foi possível excluir o documento agora.")
                else:
                    st.rerun()
        st.subheader("Cobertura documental")
        coverage=document_coverage(docs,CURRENT_YEAR); st.dataframe(coverage,use_container_width=True,hide_index=True)

elif page == "Central de Relatórios":
    header("Central de Relatórios","Escolha o relatório que você precisa sem navegar por várias telas.")
    r1,r2,r3=st.columns(3)
    with r1:
        st.subheader("Fechamento")
        st.caption("Receitas, despesas, documentos e checklist do mês.")
        if st.button("Abrir Fechamento Mensal",use_container_width=True): st.session_state["_navigate_to"]="Fechamento Mensal"; st.rerun()
    with r2:
        st.subheader("Financeiro")
        st.caption("Evolução, margem, categorias e consistência.")
        if st.button("Abrir Análise Financeira",use_container_width=True): st.session_state["_navigate_to"]="Análise Financeira"; st.rerun()
    with r3:
        st.subheader("MEI")
        st.caption("Relatório Mensal e preparação da DASN-SIMEI.")
        if st.button("Abrir Relatório Mensal",use_container_width=True): st.session_state["_navigate_to"]="Relatório Mensal"; st.rerun()
    st.info("Cada relatório é calculado com os dados registrados no Razync Pro. Confira informações fiscais antes de enviar declarações oficiais.")

elif page == "Assistente Razync":
    header("Assistente Razync","Faça perguntas simples sobre os dados que já estão no sistema.")
    prompts=["Quanto ainda posso faturar?","Qual é o meu resultado?","Quanto gastei?","Tenho DAS atrasado?","Como estão minhas notas?"]
    q=st.text_input("Pergunte sobre seu MEI",placeholder="Ex.: Quanto ainda posso faturar neste ano?")
    choice=st.selectbox("Ou escolha uma pergunta",["Escolha..."]+prompts)
    if choice!="Escolha...": q=choice
    if q:
        st.success(assistant_answer(q,transactions,invoices,das_rows,limit,CURRENT_YEAR))
    st.caption("As respostas usam os registros do Razync Pro e não substituem análise profissional ou consulta aos portais oficiais.")

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
    header("Meu MEI","Cadastre os dados usados nos relatórios e alertas.")
    with st.form("profile_form"):
        cnpj=st.text_input("CNPJ",value=str(profile.get("cnpj") or "")); business=st.text_input("Razão social",value=str(profile.get("business_name") or "")); trade=st.text_input("Nome fantasia",value=str(profile.get("trade_name") or "")); activity=st.text_input("Atividade principal",value=str(profile.get("main_activity") or "")); activity_type=st.selectbox("Tipo de atividade",["Serviços","Comércio","Indústria","Misto"],index=["Serviços","Comércio","Indústria","Misto"].index(profile.get("activity_type") if profile.get("activity_type") in ["Serviços","Comércio","Indústria","Misto"] else "Serviços")); opening_date=st.date_input("Data de abertura",value=opening or date.today()); annual_limit=st.number_input("Limite anual personalizado (opcional)",min_value=0.0,value=float(profile.get("annual_limit") or MEI_ANNUAL_LIMIT),step=1000.0); city=st.text_input("Município",value=str(profile.get("city") or "")); state=st.text_input("UF",value=str(profile.get("state") or ""),max_chars=2); phone=st.text_input("Telefone",value=str(profile.get("phone") or "")); municipal=st.text_input("Inscrição municipal",value=str(profile.get("municipal_registration") or "")); state_reg=st.text_input("Inscrição estadual",value=str(profile.get("state_registration") or "")); has_employee=st.checkbox("Possui empregado",value=bool(profile.get("has_employee",False)))
        if st.form_submit_button("Salvar dados",use_container_width=True): save_profile(uid,cnpj=cnpj,business_name=business,trade_name=trade,main_activity=activity,activity_type=activity_type,opening_date=opening_date,annual_limit=annual_limit,city=city,state=state.upper(),phone=phone,municipal_registration=municipal,state_registration=state_reg,has_employee=has_employee); st.success("Dados salvos."); st.rerun()

elif page == "Status do Sistema":
    header("Status do Sistema","Veja se o Razync está usando uma infraestrutura adequada para produção.")
    runtime=database_runtime_info()
    c1,c2,c3=st.columns(3)
    c1.metric("Banco",runtime["backend"]); c2.metric("Persistência","Ativa" if runtime["persistent"] else "Temporária"); c3.metric("Produção","Pronto" if runtime["production_ready"] else "Configuração necessária")
    if runtime["persistent"]: st.success("O banco configurado é persistente.")
    else: st.warning("O app está usando SQLite temporário. No Streamlit Cloud, configure DATABASE_URL com PostgreSQL/Supabase antes de colocar clientes reais.")
    st.subheader("Integrações")
    st.write("• PostgreSQL/Supabase:","configurado" if runtime["persistent"] else "pendente")
    st.write("• NFS-e Nacional: preparação funcional; credenciais/API externa pendentes")
    st.write("• Integrações bancárias diretas: pendentes; importação de arquivo já disponível")
    st.write("• Documentos: Supabase Storage privado quando a conta usa Supabase Auth; fallback legado durante a migração")

elif page == "Backup":
    header("Backup","Baixe um pacote dos dados para manter uma cópia independente.")
    backup=build_backup_zip(profile,transactions,invoices,das_rows,obligations,contacts,employees,docs,lambda doc_id:(lambda d: {**d, "content": document_bytes(d)} if d else None)(get_document(uid,doc_id)))
    st.download_button("Baixar backup completo (.zip)",backup,file_name=f"backup_razync_{date.today().isoformat()}.zip",mime="application/zip",use_container_width=True)
    st.caption("O pacote inclui dados em CSV/JSON e os documentos salvos no Razync Pro.")

st.divider()
st.caption("Razync Pro • Ecossistema Razync • ferramenta de organização contábil e financeira para MEI")