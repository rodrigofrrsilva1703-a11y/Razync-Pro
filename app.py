from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    add_contact, add_employee, add_invoice, add_obligation, add_transaction,
    authenticate, create_user, delete_contact, delete_document, delete_employee,
    delete_invoice, delete_obligation, delete_transaction, get_document, get_profile,
    init_db, list_contacts, list_das, list_documents, list_employees, list_invoices,
    list_obligations, list_transactions, save_document, save_profile,
    update_obligation_status, update_transaction, upsert_das, link_transaction_document,
    dashboard_financial_summary, transaction_document_numbers, count_transactions, list_transactions_page,
    load_user_snapshot, data_version, DatabaseConnectionError, resolve_supabase_user,
    resolve_trusted_developer_user, add_recurring_transaction, delete_recurring_transaction, list_recurring_transactions,
    materialize_due_recurring, set_recurring_transaction_active, list_audit_logs, add_transactions_bulk,
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
from backup_tools import backup_checksum, build_backup_zip, document_coverage
from onboarding_tools import onboarding_progress, recommended_setup, first_session_plan
from reconciliation_tools import smart_invoice_matches, duplicate_groups
from automation_tools import financial_projection, upcoming_deadlines
from ui_system import inject_design_system, page_header, section, business_card, alert_card, empty_state, helper_note, apply_plot_theme, tokens
from ui_helpers import MONTH_NAMES_PT, filter_transactions, paginate_frame
from login_security import login_attempt_guard
from storage_service import download_document, remove_document, upload_document
from growth_tools import (
    build_notifications, checkout_url, integration_readiness, normalize_nfse,
    notification_calendar, read_nfse_export, suggest_nfse_columns,
)
from automation_suite import (
    automation_overview, das_payment_matches, learned_category,
)
from auth_service import (
    AuthServiceError, is_supabase_auth_configured, reset_password,
    github_authorization_url, github_sign_in, is_developer_github_configured,
    restore_session as supabase_restore_session,
    sign_in as supabase_sign_in, sign_out as supabase_sign_out,
    sign_up as supabase_sign_up, update_password as supabase_update_password,
)
from session_persistence import (
    clear_persisted_session, persist_refresh_token,
    persistent_session_controller, read_refresh_token,
)
from brand_assets import brand_logo_data_uri, ensure_brand_assets
from document_intelligence import CATEGORIES as DOCUMENT_CATEGORIES, analyze_document
from demo_mode import render_demo
from legal_content import PRIVACY_NOTICE, PRIVACY_VERSION, TERMS_OF_USE
from customer_experience import (
    OFFICIAL_SERVICES, build_today_plan, das_journey, financial_story,
    integration_catalog, next_onboarding_step, security_checklist,
    transaction_restore_payload,
)
from navigation_config import SIDEBAR_LABELS, SIDEBAR_GROUPS, SIDEBAR_SECONDARY_GROUPS, SIDEBAR_ICONS
from finance_workspace import render_finance_workspace
from fiscal_workspace import render_fiscal_workspace
from workspace_style import inject_workspace_style
from compact_cards import inject_compact_cards
from dashboard_workspace import render_dashboard_workspace
from sidebar_workspace import render_sidebar
from productivity_workspace import render_productivity_workspace
from account_workspace import render_account_workspace
from assistant_workspace import render_ai_assistant
from fiscal_automation import analyze_das_guide
from validators import valid_cnpj, valid_cpf, cpf_or_cnpj_status, valid_competence
from commercial_readiness import PLAN_CATALOG, integration_maturity, production_checklist
from monitoring import safe_error

CURRENT_YEAR = date.today().year
BRAND_LOGO_PATH = ensure_brand_assets()
BRAND_LOGO_DATA_URI = brand_logo_data_uri()

st.set_page_config(page_title="Razync Pro", page_icon=BRAND_LOGO_PATH, layout="wide", initial_sidebar_state="expanded")
try:
    init_db()
except DatabaseConnectionError as exc:
    safe_error("database_init_failed", exc, operation="init_db", backend="database")
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
inject_workspace_style()


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def header(title: str, subtitle: str) -> None:
    current_page = str(globals().get("page", title))
    page_header(title, subtitle, eyebrow=f"{group_for_page(current_page)} • Razync Pro")


def alert_box(level: str, title: str, text: str) -> None:
    alert_card(level, title, text)


def navigate_to(destination: str) -> None:
    st.session_state["_navigate_to"] = destination
    st.rerun()


def refresh_snapshot() -> None:
    st.session_state.pop(_snapshot_key, None)
    st.session_state.pop(_snapshot_version_key, None)
    st.toast("Dados atualizados com segurança.")
    st.rerun()


def secret_value(name: str) -> str:
    try:
        return str(st.secrets.get(name, ""))
    except Exception:
        return ""


def logout_current_user() -> None:
    """Close the active session and return safely to the login screen."""
    auth_enabled = is_supabase_auth_configured()
    session_controller = persistent_session_controller() if auth_enabled else None
    if session_controller is not None:
        clear_persisted_session(session_controller)
    if auth_enabled:
        try:
            supabase_sign_out(
                st.session_state.get("access_token", ""),
                st.session_state.get("refresh_token", ""),
            )
        except AuthServiceError:
            pass
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


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
    session_controller = persistent_session_controller() if auth_enabled else None

    if (
        auth_enabled
        and session_controller is not None
        and "user" not in st.session_state
        and not st.session_state.get("_persistent_session_checked")
    ):
        st.session_state["_persistent_session_checked"] = True
        saved_refresh_token = read_refresh_token(session_controller)
        if saved_refresh_token:
            try:
                identity = supabase_restore_session(saved_refresh_token)
                user = resolve_supabase_user(
                    identity["auth_user_id"],
                    identity["email"],
                    identity.get("name", ""),
                )
            except (AuthServiceError, DatabaseConnectionError, ValueError):
                clear_persisted_session(session_controller)
            else:
                st.session_state["access_token"] = identity["access_token"]
                st.session_state["refresh_token"] = identity["refresh_token"]
                st.session_state["user"] = user
                persist_refresh_token(session_controller, identity["refresh_token"])
                st.rerun()

    oauth_state = str(st.query_params.get("state", ""))
    oauth_code = str(st.query_params.get("code", ""))
    if (
        "user" not in st.session_state
        and is_developer_github_configured()
        and oauth_code
        and oauth_state.startswith("rzgh.")
    ):
        try:
            identity = github_sign_in(oauth_code, oauth_state)
            user = resolve_trusted_developer_user(
                identity["auth_user_id"], identity["email"], identity["name"]
            )
        except (AuthServiceError, DatabaseConnectionError, ValueError) as exc:
            st.error(str(exc))
        else:
            st.session_state["auth_provider"] = "github"
            st.session_state["github_login"] = identity["github_login"]
            st.session_state["user"] = user
            st.query_params.clear()
            st.rerun()

    if "user" in st.session_state:
        return st.session_state["user"]

    if st.session_state.get("_demo_mode"):
        render_demo()
        st.stop()

    st.markdown(
        f"""
        <div class="rz-login-shell">
          <div class="rz-login-brand">
            <img class="rz-login-mark" src="{BRAND_LOGO_DATA_URI}" alt="Logo Razync Pro">
            <div><strong>Razync</strong><span>PRO</span></div>
          </div>
          <div class="rz-login-kicker">Gestão inteligente para MEI</div>
          <h1>Menos planilhas.<br><em>Mais controle do seu MEI.</em></h1>
          <p class="rz-login-lead">Organize o financeiro, acompanhe obrigações e mantenha seus documentos prontos para decidir com tranquilidade.</p>
          <div class="rz-login-benefits">
            <span><b>01</b> Financeiro em dia</span>
            <span><b>02</b> Alertas fiscais</span>
            <span><b>03</b> Dados protegidos</span>
          </div>
          <div class="rz-login-proof">
            <span>Feito para a rotina real do MEI</span><i></i><span>Simples de começar</span>
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

    if st.button("Conhecer o Razync com dados de exemplo", width="stretch"):
        st.session_state["_demo_mode"] = True
        st.rerun()
    st.markdown(
        '<p class="rz-demo-note">Sem cadastro · dados fictícios · nenhuma informação é salva</p>',
        unsafe_allow_html=True,
    )

    login_tab, signup_tab, recovery_tab = st.tabs(
        ["Entrar", "Criar minha conta", "Recuperar acesso"]
    )

    with login_tab:
        st.markdown('<div class="rz-auth-heading"><strong>Acesse sua conta</strong><span>Use seu e-mail e senha para continuar de onde parou.</span></div>', unsafe_allow_html=True)
        if is_developer_github_configured():
            st.link_button(
                "Acesso administrativo com GitHub",
                github_authorization_url(),
                width="stretch",
                type="primary",
            )
            st.caption(
                "Acesso administrativo protegido e liberado somente para a conta autorizada."
            )
            st.divider()
        with st.form("login_form"):
            email = st.text_input(
                "E-mail", placeholder="voce@exemplo.com", key="login_email"
            ).strip()
            password = st.text_input(
                "Senha", type="password", placeholder="Digite sua senha", key="login_password"
            )
            keep_connected = st.checkbox(
                "Continuar conectado neste dispositivo",
                value=True,
                disabled=session_controller is None,
                help="Sua sessão é renovada pelo Supabase e removida ao sair.",
            )
            submitted = st.form_submit_button("Entrar", width="stretch")

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
                        if (
                            auth_enabled
                            and keep_connected
                            and session_controller is not None
                        ):
                            persist_refresh_token(
                                session_controller,
                                st.session_state["refresh_token"],
                            )
                        st.rerun()

                    retry_after = login_attempt_guard.record_failure(email)
                    if retry_after:
                        minutes = max(1, (retry_after + 59) // 60)
                        st.error(f"Muitas tentativas. Tente novamente em {minutes} minuto(s).")
                    else:
                        st.error("E-mail ou senha inválidos, ou e-mail ainda não confirmado.")

    with signup_tab:
        st.markdown('<div class="rz-auth-heading"><strong>Crie sua conta</strong><span>É rápido: informe seus dados para começar a organizar seu MEI.</span></div>', unsafe_allow_html=True)
        with st.form("signup_form"):
            name = st.text_input("Nome", placeholder="Como podemos chamar você?", key="signup_name").strip()
            email = st.text_input("E-mail", placeholder="voce@exemplo.com", key="signup_email").strip()
            password = st.text_input(
                "Senha", type="password", key="signup_password",
                help="Use pelo menos 8 caracteres.",
            )
            confirmation = st.text_input(
                "Confirmar senha", type="password",
                key="signup_password_confirmation",
            )
            consent = st.checkbox(
                f"Li e aceito os Termos de Uso e a Política de Privacidade (versão {PRIVACY_VERSION}).",
                key="signup_legal_consent",
            )
            submitted = st.form_submit_button("Criar conta", width="stretch")

        if submitted:
            if not consent:
                st.error("Aceite os Termos de Uso e a Política de Privacidade para criar a conta.")
            elif password != confirmation:
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
        st.markdown('<div class="rz-auth-heading"><strong>Recupere o acesso</strong><span>Informe o e-mail da sua conta. Enviaremos o próximo passo.</span></div>', unsafe_allow_html=True)
        if auth_enabled:
            with st.form("password_recovery_form"):
                email = st.text_input("E-mail", key="recovery_email").strip()
                submitted = st.form_submit_button(
                    "Enviar recuperação", width="stretch"
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

    with st.expander("Privacidade e Termos de Uso"):
        st.markdown(PRIVACY_NOTICE)
        st.markdown(TERMS_OF_USE)
        st.caption(f"Versão vigente: {PRIVACY_VERSION}")
    st.markdown('<div class="rz-login-security">🔒 Conexão segura · seus dados permanecem privados</div>', unsafe_allow_html=True)
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
        rows.append({"month":month,"month_name":MONTH_NAMES_PT[month - 1],"with_doc":with_doc,"without_doc":without_doc,"services":services,"sales":sales,"total":total})
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
        rows.append({"Mês": MONTH_NAMES_PT[month - 1], "Entradas": entradas, "Saídas": saidas, "Resultado": entradas-saidas})
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
generated_recurring = materialize_due_recurring(uid)
if generated_recurring:
    st.toast(f"{generated_recurring} lançamento(s) recorrente(s) gerado(s).", icon="✓")

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

# Um único padrão de densidade para todas as ferramentas após a autenticação.
inject_compact_cards()


st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--rz-border);
        background: var(--rz-surface);
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1.05rem .85rem 1.1rem;
    }
    .rz-side-brand {
        display: flex;
        align-items: center;
        gap: .72rem;
        padding: .12rem .38rem .72rem;
        margin-bottom: .18rem;
    }
    .rz-side-brand img {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        object-fit: cover;
        box-shadow: 0 5px 14px rgba(3, 174, 238, .17);
    }
    .rz-side-brand strong {
        color: var(--rz-text);
        font-size: 1.08rem;
        letter-spacing: -.025em;
    }
    .rz-side-brand em {
        margin-left: .28rem;
        color: var(--rz-primary);
        font-size: .62rem;
        font-style: normal;
        font-weight: 800;
        letter-spacing: .09em;
        vertical-align: .12rem;
    }
    .rz-side-brand span {
        display: block;
        max-width: 185px;
        margin-top: .1rem;
        overflow: hidden;
        color: var(--rz-muted);
        font-size: .7rem;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .st-key-sidebar_navigation [data-testid="stButton"] {
        margin: .06rem 0;
    }
    .st-key-sidebar_navigation [data-testid="stButton"] button {
        min-height: 2.35rem;
        justify-content: flex-start;
        gap: .68rem;
        padding: .38rem .62rem;
        border: 0 !important;
        border-radius: 11px;
        color: var(--rz-muted);
        background: transparent;
        box-shadow: none !important;
        transition: background .15s ease, color .15s ease;
    }
    .st-key-sidebar_navigation [data-testid="stButton"] button:hover {
        color: var(--rz-text);
        background: var(--rz-soft);
    }
    .st-key-sidebar_navigation [data-testid="stButton"] button:disabled {
        color: var(--rz-text) !important;
        background: color-mix(in srgb, var(--rz-muted) 13%, transparent) !important;
        opacity: 1 !important;
        cursor: default;
    }
    .st-key-sidebar_navigation [data-testid="stButton"] button p {
        font-size: .84rem;
        font-weight: 530;
        letter-spacing: -.004em;
    }
    .st-key-sidebar_navigation [data-testid="stButton"] button span {
        color: currentColor;
        font-size: 1.22rem;
    }
    .st-key-sidebar_navigation [data-testid="stExpander"] {
        margin: .08rem 0;
        border: 0;
        background: transparent;
    }
    .st-key-sidebar_navigation [data-testid="stExpander"] summary {
        min-height: 2.4rem;
        padding: .34rem .5rem;
        border-radius: 11px;
        color: var(--rz-text);
        font-size: .92rem;
        font-weight: 650;
    }
    .st-key-sidebar_navigation [data-testid="stExpander"] summary:hover {
        background: var(--rz-soft);
    }
    .st-key-sidebar_navigation [data-testid="stExpander"] details > div {
        padding-left: .35rem;
        border-left: 1px solid var(--rz-border);
    }
    [data-testid="stSidebar"] hr {
        margin: .78rem 0;
        border-color: var(--rz-border);
    }
    [data-testid="stSidebar"] details {
        border: 0;
        background: transparent;
    }
    [data-testid="stSidebar"] details summary {
        border-radius: 10px;
        color: var(--rz-muted);
        font-size: .88rem;
    }
    .rz-side-account {
        padding: .12rem .15rem .25rem;
        color: var(--rz-muted);
        font-size: .72rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_sidebar(
    profile=profile,
    user=user,
    transactions=transactions,
    das_rows=das_rows,
    documents=docs,
    page=page,
    brand_logo_data_uri=BRAND_LOGO_DATA_URI,
    navigate=navigate_to,
    refresh_data=refresh_snapshot,
    logout=logout_current_user,
)

undo_transaction = st.session_state.get("_undo_transaction")
if undo_transaction:
    undo_text, undo_action = st.columns([5, 1.2])
    undo_text.info(f"“{undo_transaction.get('description') or 'Lançamento'}” foi excluído. Você pode desfazer esta ação enquanto estiver conectado.")
    if undo_action.button("Desfazer", key="undo_deleted_transaction", width="stretch"):
        try:
            add_transaction(uid, **transaction_restore_payload(undo_transaction))
        except Exception:
            st.error("Não foi possível restaurar o lançamento.")
        else:
            st.session_state.pop("_undo_transaction", None)
            st.success("Lançamento restaurado.")
            st.rerun()

# Dashboard V2 uses only the local snapshot while navigating.
if page == "Dashboard":
    business_label = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"
    cnpj_label = str(profile.get("cnpj") or "").strip() or None
    header("Visão geral", "O que importa hoje para manter seu MEI organizado.")
    business_card(business_label, CURRENT_YEAR, cnpj_label)
    render_dashboard_workspace(
        profile=profile, transactions=transactions, invoices=invoices,
        das_rows=das_rows, obligations=obligations, documents=docs,
        annual_limit=limit, annual_revenue=year_revenue, current_year=CURRENT_YEAR,
        brl=brl, navigate=navigate_to,
    )

elif page == "Produtividade":
    header("Produtividade", "Automações, alertas e assistência em uma única área.")
    render_productivity_workspace(navigate=navigate_to)

elif page == "Conta e Sistema":
    header("Conta e sistema", "Dados, privacidade, segurança e operação do Razync Pro.")
    render_account_workspace(
        navigate=navigate_to,
        developer_access=st.session_state.get("auth_provider") == "github",
    )

elif page == "Financeiro":
    header("Financeiro", "Controle entradas, saídas, conciliação e análise em uma única área.")
    render_finance_workspace(
        transactions=transactions,
        invoices=invoices,
        annual_limit=limit,
        current_year=CURRENT_YEAR,
        theme=UI_THEME,
        brl=brl,
        navigate=navigate_to,
    )

elif page == "Movimentações":
    header("Movimentações","Registre o que entrou e saiu do MEI. Comece pelo essencial; os detalhes ficam opcionais.")
    with st.container(border=True):
        st.caption("NOVO LANÇAMENTO")
        with st.form("tx_form", clear_on_submit=True):
            tx_type = st.segmented_control(
                "Tipo do lançamento",
                ["Receita", "Despesa"],
                default="Receita",
                selection_mode="single",
                format_func=lambda option: "Entrada · Receita" if option == "Receita" else "Saída · Despesa",
                key="tx_type_new",
                width="stretch",
            ) or "Receita"
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
            submitted = st.form_submit_button("Salvar movimentação", type="primary", width="stretch")
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
        f1, f2, f3 = st.columns([1, 1, 2])
        type_filter = f1.selectbox("Filtrar por tipo", ["Todos", "Receita", "Despesa"])
        category_options = ["Todas"] + sorted(str(x) for x in transactions["category"].dropna().unique())
        category_filter = f2.selectbox("Filtrar por categoria", category_options)
        search_filter = f3.text_input("Buscar no histórico", placeholder="Descrição, cliente ou documento")
        filtered_view = filter_transactions(
            transactions,
            tx_type=type_filter,
            category=category_filter,
            search=search_filter,
        )
        view, total_tx, current_tx_page, max_tx_page = paginate_frame(
            filtered_view,
            st.session_state.get("tx_history_page", 1),
            page_size=50,
        )
        page_size = 50
        st.caption(f"{total_tx} lançamento(s) encontrado(s) no histórico completo.")
        view["Data"] = view["tx_date"].dt.date; view["Tipo"] = view["tx_type"]; view["Descrição"] = view["description"]; view["Categoria"] = view["category"]; view["Valor"] = view["value"]
        st.dataframe(view[["id","Data","Tipo","Descrição","Categoria","Valor"]], width="stretch", hide_index=True, column_config={"id":None,"Valor":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"Data":st.column_config.DateColumn("Data",format="DD/MM/YYYY")})
        if total_tx > page_size:
            pprev, pinfo, pnext = st.columns([1,2,1])
            if pprev.button("← Anterior", disabled=current_tx_page <= 1, width="stretch"):
                st.session_state["tx_history_page"] = current_tx_page - 1; st.rerun()
            pinfo.caption(f"Página {current_tx_page} de {max_tx_page} • {total_tx} lançamentos")
            if pnext.button("Próxima →", disabled=current_tx_page >= max_tx_page, width="stretch"):
                st.session_state["tx_history_page"] = current_tx_page + 1; st.rerun()
        with st.expander("Editar um lançamento"):
            edit_id = st.selectbox("Lançamento", transactions["id"].tolist(), format_func=lambda x: f"#{x} - {transactions.loc[transactions['id']==x,'description'].iloc[0]}", key="edit_tx_id")
            edit_row = transactions.loc[transactions["id"] == edit_id].iloc[0]
            with st.form("edit_tx_form"):
                e1, e2 = st.columns(2)
                edit_type = e1.selectbox("Tipo", ["Receita", "Despesa"], index=0 if edit_row["tx_type"] == "Receita" else 1)
                edit_date = e2.date_input("Data", value=edit_row["tx_date"].date())
                edit_description = st.text_input("Descrição", value=str(edit_row["description"] or ""))
                e1, e2 = st.columns(2)
                edit_category = e1.text_input("Categoria", value=str(edit_row["category"] or ""))
                edit_value = e2.number_input("Valor", min_value=0.01, value=float(edit_row["value"]), step=10.0)
                e1, e2 = st.columns(2)
                edit_counterparty = e1.text_input("Cliente ou fornecedor", value=str(edit_row["counterparty"] or ""))
                edit_document = e2.text_input("Nota ou documento", value=str(edit_row["document_number"] or ""))
                edit_payment = st.text_input("Forma de pagamento", value=str(edit_row["payment_method"] or ""))
                save_edit = st.form_submit_button("Salvar alterações", type="primary", width="stretch")
            if save_edit:
                if not edit_description.strip():
                    st.error("Informe uma descrição.")
                else:
                    update_transaction(uid, int(edit_id), tx_date=edit_date, tx_type=edit_type, description=edit_description.strip(), category=edit_category.strip() or "Outros", value=edit_value, document_number=edit_document.strip(), counterparty=edit_counterparty.strip(), payment_method=edit_payment.strip())
                    st.success("Lançamento atualizado.")
                    st.rerun()
        with st.expander("Excluir um lançamento"):
            item = st.selectbox("Selecione", transactions["id"].tolist(), format_func=lambda x: f"#{x} - {transactions.loc[transactions['id']==x,'description'].iloc[0]}")
            st.caption("A exclusão é definitiva. Confira o lançamento antes de continuar.")
            if st.button("Excluir lançamento selecionado", width="stretch"):
                deleted = transactions.loc[transactions["id"] == item].iloc[0].to_dict()
                st.session_state["_undo_transaction"] = transaction_restore_payload(deleted)
                delete_transaction(uid, int(item))
                st.rerun()

elif page == "Recorrências":
    header(
        "Lançamentos recorrentes",
        "Cadastre receitas e despesas que se repetem. O Razync gera cada ocorrência na data correta.",
    )
    with st.container(border=True):
        st.caption("NOVA RECORRÊNCIA")
        with st.form("recurring_form", clear_on_submit=True):
            recurring_type = st.segmented_control(
                "Tipo", ["Receita", "Despesa"], default="Despesa", selection_mode="single"
            ) or "Despesa"
            r1, r2 = st.columns(2)
            recurring_description = r1.text_input("Descrição", placeholder="Ex.: aluguel, internet, mensalidade")
            recurring_value = r2.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
            r1, r2, r3 = st.columns(3)
            recurring_category = r1.selectbox(
                "Categoria",
                ["Serviços", "Vendas", "Materiais", "Aluguel", "Transporte", "Taxas", "Marketing", "Pró-labore/Retirada", "Outros"],
            )
            recurring_frequency = r2.selectbox("Frequência", ["Mensal", "Semanal", "Anual"])
            recurring_payment = r3.selectbox(
                "Forma de pagamento", ["PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro"]
            )
            r1, r2 = st.columns(2)
            recurring_start = r1.date_input("Primeira ocorrência", value=date.today())
            has_end = r2.checkbox("Definir data final")
            recurring_end = r2.date_input(
                "Data final",
                value=date.today(),
                disabled=not has_end,
            )
            save_recurring = st.form_submit_button(
                "Salvar recorrência", type="primary", width="stretch"
            )
        if save_recurring:
            if not recurring_description.strip():
                st.error("Informe uma descrição.")
            elif recurring_value <= 0:
                st.error("Informe um valor maior que zero.")
            elif has_end and recurring_end < recurring_start:
                st.error("A data final não pode ser anterior à primeira ocorrência.")
            else:
                add_recurring_transaction(
                    uid,
                    tx_type=recurring_type,
                    description=recurring_description.strip(),
                    category=recurring_category,
                    value=recurring_value,
                    payment_method=recurring_payment,
                    frequency=recurring_frequency,
                    next_date=recurring_start,
                    end_date=recurring_end if has_end else None,
                    active=True,
                )
                materialize_due_recurring(uid)
                st.success("Recorrência criada.")
                st.rerun()

    recurring_items = list_recurring_transactions(uid)
    section("Recorrências cadastradas")
    if not recurring_items:
        empty_state(
            "Nenhuma recorrência cadastrada",
            "Cadastre um pagamento ou recebimento frequente para reduzir lançamentos manuais.",
            "↻",
        )
    else:
        recurring_df = pd.DataFrame(recurring_items)
        recurring_df["Situação"] = recurring_df["active"].map({True: "Ativa", False: "Pausada"})
        st.dataframe(
            recurring_df[["id", "description", "tx_type", "value", "frequency", "next_date", "Situação"]],
            width="stretch",
            hide_index=True,
            column_config={
                "id": None,
                "description": "Descrição",
                "tx_type": "Tipo",
                "value": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "frequency": "Frequência",
                "next_date": st.column_config.DateColumn("Próxima ocorrência", format="DD/MM/YYYY"),
            },
        )
        labels = {
            int(item["id"]): f"#{item['id']} · {item['description']} · {brl(float(item['value']))}"
            for item in recurring_items
        }
        selected_recurring = st.selectbox(
            "Gerenciar recorrência",
            list(labels),
            format_func=lambda item_id: labels[item_id],
        )
        selected_item = next(
            item for item in recurring_items if int(item["id"]) == int(selected_recurring)
        )
        manage1, manage2 = st.columns(2)
        toggle_label = "Pausar recorrência" if selected_item["active"] else "Reativar recorrência"
        if manage1.button(toggle_label, width="stretch"):
            set_recurring_transaction_active(uid, int(selected_recurring), not selected_item["active"])
            st.rerun()
        if manage2.button("Excluir recorrência", width="stretch"):
            delete_recurring_transaction(uid, int(selected_recurring))
            st.rerun()

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
                st.dataframe(raw.head(8), width="stretch", hide_index=True)
                cols = list(raw.columns)
                a,b,c = st.columns(3)
                date_col = a.selectbox("Coluna de data", cols, index=0)
                desc_col = b.selectbox("Coluna de descrição", cols, index=min(1,len(cols)-1))
                value_col = c.selectbox("Coluna de valor", cols, index=min(2,len(cols)-1))
                st.subheader("2. Prepare a importação")
                prepared = prepare_statement(raw, date_col, desc_col, value_col)
                learned_suggestions = [
                    learned_category(
                        row["description"], row["tx_type"], transactions,
                        suggest_category(row["description"]),
                    )
                    for _, row in prepared.iterrows()
                ]
                prepared["Categoria sugerida"] = [item["category"] for item in learned_suggestions]
                prepared["Confiança da categoria"] = [item["confidence"] for item in learned_suggestions]
                if prepared.empty:
                    st.warning("Nenhuma linha válida foi encontrada com esse mapeamento.")
                else:
                    existing_keys = set()
                    if not transactions.empty:
                        existing_keys = set((r.tx_date.date() if hasattr(r.tx_date,"date") else r.tx_date, r.description, float(r.value), r.tx_type) for r in transactions.itertuples())
                    prepared["Duplicado"] = [is_probable_duplicate(existing_keys,row.tx_date,row.description,row.value,row.tx_type) for row in prepared.itertuples()]
                    st.dataframe(prepared, width="stretch", hide_index=True, column_config={"value":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"tx_date":st.column_config.DateColumn("Data",format="DD/MM/YYYY")})
                    only_new = st.checkbox("Ignorar possíveis duplicados", value=True)
                    rows_to_import = prepared[~prepared["Duplicado"]] if only_new else prepared
                    st.caption(f"{len(rows_to_import)} lançamento(s) serão importados.")
                    if st.button("Confirmar importação", type="primary", width="stretch"):
                        import_rows=[{
                            "tx_date":r["tx_date"],
                            "tx_type":r["tx_type"],
                            "description":r["description"],
                            "category":r["Categoria sugerida"],
                            "value":float(r["value"]),
                            "document_number":"",
                            "counterparty":"",
                            "payment_method":"Banco",
                        } for _,r in rows_to_import.iterrows()]
                        try:
                            count=add_transactions_bulk(uid,import_rows)
                        except Exception:
                            st.error("A importação foi cancelada e nenhum lançamento foi salvo. Revise o arquivo e tente novamente.")
                        else:
                            st.success(f"{count} lançamento(s) importados em uma única operação.")
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
        st.dataframe(show_matches[["Nota","Cliente","Valor da nota","Data do lançamento","Lançamento","Valor lançado","Confiança","Pontuação","Motivos"]], width="stretch", hide_index=True, column_config={"Valor da nota":st.column_config.NumberColumn("Valor da nota", format="R$ %.2f"), "Valor lançado":st.column_config.NumberColumn("Valor lançado", format="R$ %.2f"), "Data do lançamento":st.column_config.DateColumn("Data do lançamento", format="DD/MM/YYYY"), "Pontuação":st.column_config.ProgressColumn("Pontuação", min_value=0, max_value=100)})
        option_labels = {int(r.tx_id): f"Nota {r.invoice_number or r.invoice_id} → {r.tx_description} • R$ {r.tx_value:,.2f} • confiança {r.confidence}" for r in matches.itertuples()}
        selected_tx = st.selectbox("Sugestão para revisar", list(option_labels.keys()), format_func=lambda x: option_labels[x], key="smart_match")
        selected = matches[matches["tx_id"] == selected_tx].iloc[0]
        st.caption(f"Motivos: {selected['reasons']} • pontuação {int(selected['score'])}/100")
        if st.button("Confirmar vínculo com este lançamento", type="primary", width="stretch"):
            link_transaction_document(uid, int(selected["tx_id"]), str(selected["invoice_number"] or ""), str(selected["customer"] or ""))
            st.success("Nota vinculada ao lançamento existente sem criar receita duplicada.")
            st.rerun()

    section("Notas ainda sem vínculo")
    pending_inv = rec["pending_invoices"]
    if pending_inv.empty:
        st.success("Todas as notas numeradas estão conciliadas com receitas cadastradas.")
    else:
        st.dataframe(pending_inv, width="stretch", hide_index=True, column_config={"Valor":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        with st.expander("Criar receita a partir de uma nota sem correspondência"):
            selected_invoice = st.selectbox("Nota", pending_inv["ID"].tolist(), key="rec_invoice")
            source = invoices[invoices["id"] == selected_invoice].iloc[0]
            st.caption("Use somente quando não existir um recebimento correspondente entre as movimentações.")
            if st.button("Criar nova receita desta nota", width="stretch"):
                issue = source["issue_date"]
                tx_date_value = issue.date() if hasattr(issue, "date") else issue
                add_transaction(uid, tx_date=tx_date_value, tx_type="Receita", description=source.get("description") or f"Nota {source.get('number') or ''}", category="Serviços" if source.get("invoice_type") == "Serviço" else "Vendas", value=float(source.get("amount") or 0), document_number=str(source.get("number") or ""), counterparty=str(source.get("customer") or ""), payment_method="Outro")
                st.rerun()

    section("Possíveis lançamentos duplicados")
    if duplicates.empty:
        st.success("Nenhuma duplicidade evidente foi encontrada nas movimentações.")
    else:
        st.dataframe(duplicates, width="stretch", hide_index=True, column_config={"tx_date":st.column_config.DateColumn("Data", format="DD/MM/YYYY"), "value":st.column_config.NumberColumn("Valor", format="R$ %.2f")})
        with st.expander("Remover duplicidade"):
            duplicate_id = st.selectbox("Lançamento a excluir", duplicates["id"].tolist(), key="duplicate_delete")
            st.caption("Confira os registros antes de excluir. A exclusão é definitiva.")
            if st.button("Excluir lançamento selecionado", width="stretch"):
                deleted = transactions.loc[transactions["id"] == duplicate_id].iloc[0].to_dict()
                st.session_state["_undo_transaction"] = transaction_restore_payload(deleted)
                delete_transaction(uid, int(duplicate_id))
                st.rerun()

    if st.button("Importar novo extrato", width="stretch"):
        st.session_state["_navigate_to"] = "Importar Extrato"
        st.rerun()

elif page == "Fluxo de Caixa":
    header("Fluxo de Caixa","Veja entradas, saídas, resultado e saldo acumulado por mês.")
    year = st.selectbox("Ano",list(range(CURRENT_YEAR-3,CURRENT_YEAR+1)),index=3)
    cf = cashflow_monthly(transactions,year)
    c1,c2,c3 = st.columns(3)
    c1.metric("Entradas",brl(float(cf["Entradas"].sum()))); c2.metric("Saídas",brl(float(cf["Saídas"].sum()))); c3.metric("Resultado",brl(float(cf["Resultado"].sum())))
    fig = px.bar(cf,x="Mês",y=["Entradas","Saídas"],barmode="group",template=PLOT_TEMPLATE)
    apply_plot_theme(fig, UI_THEME)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.dataframe(cf,width="stretch",hide_index=True,column_config={"Entradas":st.column_config.NumberColumn(format="R$ %.2f"),"Saídas":st.column_config.NumberColumn(format="R$ %.2f"),"Resultado":st.column_config.NumberColumn(format="R$ %.2f"),"Saldo acumulado":st.column_config.NumberColumn(format="R$ %.2f")})

elif page == "Análise Financeira":
    header("Análise Financeira","Veja evolução, rentabilidade e pontos que merecem revisão antes de tomar decisões.")
    analysis_year = st.selectbox("Ano da análise", list(range(CURRENT_YEAR-3,CURRENT_YEAR+1)), index=3, key="analysis_year")
    analysis = financial_analysis(transactions, analysis_year)
    ac1,ac2,ac3,ac4 = st.columns(4)
    ac1.metric("Receitas",brl(analysis["revenue"])); ac2.metric("Despesas",brl(analysis["expense"])); ac3.metric("Resultado",brl(analysis["result"])); ac4.metric("Margem",f"{analysis['margin']:.1f}%")
    analysis_limit = annual_limit_for(opening, analysis_year, profile.get("annual_limit"))
    section("Leitura automática", "O que os números cadastrados indicam, em linguagem simples.")
    for insight in financial_story(analysis["revenue"], analysis["expense"], analysis["revenue"], analysis_limit):
        alert_card(insight["tone"], insight["title"], insight["detail"])
    monthly = analysis["monthly"]
    if not monthly.empty:
        fig = px.line(monthly,x="Mês",y=["Receitas","Despesas","Resultado"],markers=True,template=PLOT_TEMPLATE)
        apply_plot_theme(fig, UI_THEME)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.dataframe(monthly,width="stretch",hide_index=True,column_config={c:st.column_config.NumberColumn(format="R$ %.2f") for c in ["Receitas","Despesas","Resultado"]})
    st.subheader("Despesas por categoria")
    bycat = analysis["expense_categories"]
    if bycat.empty: st.info("Sem despesas registradas neste ano.")
    else:
        fig2 = px.bar(bycat, x="Categoria", y="Valor", template=PLOT_TEMPLATE)
        apply_plot_theme(fig2, UI_THEME)
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
    checks = consistency_checks(transactions,invoices,das_rows)
    st.subheader("Revisões recomendadas")
    if checks:
        for item in checks: st.warning(item)
    else: st.success("Nenhuma inconsistência relevante encontrada.")
    analysis_pdf = financial_summary_pdf(profile, analysis_year, analysis)
    st.download_button("Baixar análise financeira em PDF",analysis_pdf,file_name=f"analise_financeira_{analysis_year}.pdf",mime="application/pdf",width="stretch")

elif page == "Fechamento Mensal":
    header("Fechamento Mensal","Confira documentos, notas, movimentações e DAS antes de considerar o mês organizado.")
    c1,c2=st.columns(2)
    close_year=c1.selectbox("Ano",list(range(CURRENT_YEAR-2,CURRENT_YEAR+1)),index=2,key="close_year")
    close_month=c2.selectbox("Mês",list(range(1,13)),index=date.today().month-1,format_func=lambda m:MONTH_NAMES_PT[m - 1],key="close_month")
    closing=monthly_closing(transactions,invoices,docs,das_rows,close_year,close_month)
    a,b,c,d=st.columns(4)
    a.metric("Receitas",brl(closing["revenue"])); b.metric("Despesas",brl(closing["expense"])); c.metric("Resultado",brl(closing["result"])); d.metric("Organização",f"{closing['score']}%")
    st.progress(closing["score"]/100)
    section("Etapas do fechamento", "Resolva as pendências na ordem sugerida e volte para conferir o progresso.")
    closing_routes = {
        "Movimentações do mês revisadas": "Movimentações",
        "Receitas registradas": "Movimentações",
        "DAS da competência criado": "DAS",
        "Documentos da competência armazenados": "Documentos",
        "Lançamentos com documento informado": "Movimentações",
        "Notas fiscais conferidas": "Notas Fiscais",
    }
    for index, item in enumerate(closing["checklist"], start=1):
        status_col, detail_col, action_col = st.columns([.7, 4.8, 1.2])
        status_col.markdown("### ✓" if item["OK"] else f"### {index}")
        detail_col.write(f"**{item['Item']}**")
        detail_col.caption(item["Detalhe"])
        if not item["OK"]:
            route = closing_routes[item["Item"]]
            if action_col.button("Resolver", key=f"closing_step_{index}", width="stretch"):
                st.session_state["_navigate_to"] = route
                st.rerun()

    if closing["score"] == 100:
        st.success("Fechamento pronto: todas as etapas foram concluídas.")
    else:
        pending_count = sum(1 for item in closing["checklist"] if not item["OK"])
        st.info(f"Faltam {pending_count} etapa(s) para concluir este fechamento.")

    closing_pdf = closing_summary_pdf(profile, close_year, close_month, closing)
    st.download_button("Baixar fechamento em PDF",closing_pdf,file_name=f"fechamento_{close_year}_{close_month:02d}.pdf",mime="application/pdf",width="stretch")

elif page == "Relatório Mensal":
    header("Relatório Mensal de Receitas Brutas","Gere o relatório mensal a partir das receitas cadastradas.")
    year=st.selectbox("Ano",list(range(CURRENT_YEAR-3,CURRENT_YEAR+1)),index=3,key="rmyear")
    rows=monthly_rows(transactions,year)
    dfm=pd.DataFrame([{ "Mês":r["month_name"],"Com documento":r["with_doc"],"Sem documento":r["without_doc"],"Serviços":r["services"],"Vendas/Comércio":r["sales"],"Total":r["total"]} for r in rows])
    st.dataframe(dfm,width="stretch",hide_index=True,column_config={c:st.column_config.NumberColumn(format="R$ %.2f") for c in ["Com documento","Sem documento","Serviços","Vendas/Comércio","Total"]})
    st.caption("O relatório é gerado com base nos dados cadastrados. Guarde os documentos comprobatórios conforme as regras aplicáveis ao MEI.")
    month=st.selectbox("Mês do PDF",list(range(1,13)),format_func=lambda m:MONTH_NAMES_PT[m - 1],key="pdfmonth")
    r=rows[month-1]
    pdf=monthly_report_pdf(profile, year, [r])
    st.download_button("Baixar relatório em PDF",pdf,file_name=f"relatorio_mensal_{year}_{month:02d}.pdf",mime="application/pdf")

elif page == "Notas Fiscais":
    header("Notas Fiscais","Prepare a emissão no portal oficial, organize as notas e acompanhe cada recebimento.")
    section("Emitir NFS-e de serviço", "O Razync prepara os dados; a autorização da nota acontece no Emissor Nacional.")
    nfse_info, nfse_action = st.columns([1.8, 1])
    with nfse_info:
        st.write(f"**Prestador:** {profile.get('trade_name') or profile.get('business_name') or 'Complete os dados do MEI'}")
        st.caption(f"CNPJ: {profile.get('cnpj') or 'não cadastrado'} · Atividade: {profile.get('main_activity') or 'não cadastrada'}")
        st.caption("A emissão direta por API depende das credenciais e requisitos oficiais do Ambiente Nacional. Nenhuma senha gov.br é solicitada pelo Razync.")
    with nfse_action:
        st.link_button("Abrir Emissor Nacional", OFFICIAL_SERVICES["nfse"]["url"], type="primary", width="stretch")
        if st.button("Importar notas emitidas", key="open_nfse_import", width="stretch"):
            st.session_state["_navigate_to"] = "Importar NFS-e"
            st.rerun()

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
            submit=st.form_submit_button("Salvar nota",type="primary",width="stretch")
            if submit:
                if amount <= 0: st.error("Informe um valor maior que zero.")
                else:
                    add_invoice(uid,issue_date=issue,invoice_type=inv_type,number=number.strip(),customer=customer.strip(),customer_document=custdoc.strip(),description=desc.strip(),amount=amount,status=status); st.rerun()
    section("Notas cadastradas")
    if invoices.empty:
        empty_state("Nenhuma nota fiscal cadastrada", "Cadastre as notas emitidas para comparar faturamento, acompanhar clientes e facilitar a conciliação com os recebimentos.", "▤")
    else:
        st.dataframe(invoices,width="stretch",hide_index=True,column_config={"amount":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"issue_date":st.column_config.DateColumn("Emissão",format="DD/MM/YYYY")})
        with st.expander("Excluir uma nota"):
            iid=st.selectbox("Selecione",invoices["id"].tolist(),key="delinv"); st.caption("Confira antes de excluir: esta ação é definitiva.")
            if st.button("Excluir nota selecionada",width="stretch"): delete_invoice(uid,int(iid)); st.rerun()

elif page == "Importar NFS-e":
    header("Importar NFS-e", "Traga para o Razync as notas exportadas pelo portal da prefeitura ou pelo Emissor Nacional.")
    st.info("Exporte as notas em CSV ou XLSX. O arquivo é lido apenas durante a importação e não é armazenado.")
    nfse_file = st.file_uploader("Arquivo de NFS-e", type=["csv", "xlsx", "xls"], key="nfse_import")
    if nfse_file is not None:
        try:
            nfse_frame = read_nfse_export(nfse_file)
        except ValueError as exc:
            st.error(str(exc))
        else:
            suggestions = suggest_nfse_columns(nfse_frame.columns)
            options = ["—"] + list(nfse_frame.columns)
            labels = {"date": "Data de emissão", "number": "Número da nota", "amount": "Valor", "customer": "Cliente/tomador", "document": "CPF/CNPJ", "description": "Descrição", "status": "Situação"}
            mapping = {}
            for field, label in labels.items():
                suggested = suggestions.get(field)
                index = options.index(suggested) if suggested in options else 0
                selected = st.selectbox(label, options, index=index, key=f"nfse_{field}")
                mapping[field] = None if selected == "—" else selected
            try:
                nfse_rows = normalize_nfse(nfse_frame, mapping)
            except ValueError as exc:
                st.warning(str(exc))
                nfse_rows = []
            if nfse_rows:
                st.dataframe(pd.DataFrame(nfse_rows), width="stretch", hide_index=True)
                existing_numbers = set(invoices["number"].fillna("").astype(str)) if not invoices.empty else set()
                new_rows = [row for row in nfse_rows if row["number"] not in existing_numbers]
                st.caption(f"{len(new_rows)} nota(s) nova(s); {len(nfse_rows) - len(new_rows)} já cadastrada(s).")
                if st.button("Importar notas novas", type="primary", width="stretch", disabled=not new_rows):
                    for row in new_rows:
                        add_invoice(uid, **row)
                    st.success(f"{len(new_rows)} nota(s) importada(s).")
                    st.rerun()

elif page == "Fiscal":
    header("Fiscal MEI", "Acompanhe DAS, notas, obrigações e declaração anual sem se perder entre telas.")
    render_fiscal_workspace(
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=docs,
        current_year=CURRENT_YEAR,
        annual_limit=limit,
        annual_revenue=year_revenue,
        brl=brl,
        navigate=navigate_to,
    )

elif page == "DAS":
    header("DAS","Gere a guia no PGMEI oficial e mantenha competência, vencimento, valor, pagamento e PDF organizados no Razync.")
    year=st.selectbox("Ano",list(range(CURRENT_YEAR-2,CURRENT_YEAR+1)),index=2,key="dasyear")
    month=st.selectbox("Competência",list(range(1,13)),format_func=lambda m:f"{m:02d}/{year}",key="dasmonth")
    competence=f"{year}-{month:02d}"
    official_pgmei_url=OFFICIAL_SERVICES["das"]["url"]
    payment_suggestions = das_payment_matches(das_rows, transactions)
    journey = das_journey(competence, das_rows, docs, payment_suggestions)

    section("Andamento desta competência", "O Razync acompanha a jornada, mas nunca confirma pagamento sem sua revisão.")
    st.progress(journey["percent"] / 100)
    journey_cards = []
    for journey_step in journey["steps"]:
        state_class = "is-done" if journey_step["done"] else "is-pending"
        state_label = "Concluído" if journey_step["done"] else "Pendente"
        journey_cards.append(
            f'<div class="rz-status-step {state_class}"><strong>{escape(journey_step["title"])}</strong>'
            f'<span>{state_label} · {escape(journey_step["detail"])}</span></div>'
        )
    st.markdown('<div class="rz-status-grid">' + "".join(journey_cards) + "</div>", unsafe_allow_html=True)

    section("Emitir guia oficial", "A emissão e o pagamento acontecem no ambiente da Receita Federal; o Razync organiza o processo e guarda a guia.")
    step1,step2,step3=st.columns(3)
    step1.markdown("**1. Abra o PGMEI**")
    step1.caption("Use somente o endereço oficial da Receita Federal.")
    step2.markdown("**2. Gere o DAS**")
    step2.caption(f"Informe o CNPJ e selecione a competência {month:02d}/{year}.")
    step3.markdown("**3. Volte ao Razync**")
    step3.caption("Registre o valor e anexe o PDF emitido.")

    cnpj=str(profile.get("cnpj") or "").strip()
    if cnpj:
        st.code(cnpj,language=None)
        st.caption("CNPJ cadastrado em Meu MEI — copie para informar no portal oficial.")
    else:
        st.warning("Cadastre o CNPJ em Meu MEI antes de emitir a guia para reduzir o risco de usar dados incorretos.")
    st.link_button(
        "Gerar DAS no site oficial",
        official_pgmei_url,
        type="primary",
        width="stretch",
        help="Abre o PGMEI no domínio receita.fazenda.gov.br.",
    )
    st.caption("Por segurança, o Razync nunca pede nem armazena sua senha gov.br. Confira no pagamento o favorecido oficial e os dados do CNPJ.")

    competence_matches = [item for item in payment_suggestions if item.get("competence") == competence]
    current_das = next((item for item in das_rows if item.get("competence") == competence), None)
    if competence_matches and current_das:
        match = competence_matches[0]
        alert_card(
            "warn",
            "Possível pagamento encontrado no extrato",
            f"{match['date'].strftime('%d/%m/%Y')} · {brl(match['value'])} · confiança {match['score']}%.",
        )
        if st.button("Conferi e quero marcar como pago", key="confirm_das_match", width="stretch"):
            upsert_das(
                uid, competence, current_das.get("due_date"), float(current_das.get("amount") or match["value"]),
                "Pago", match["date"], (str(current_das.get("notes") or "") + "\nPagamento conciliado com movimentação após confirmação do usuário.").strip(),
            )
            st.success("Pagamento confirmado e controle do DAS atualizado.")
            st.rerun()

    with st.expander("Registrar a guia emitida", expanded=not bool(das_rows)):
        due=st.date_input("Vencimento da guia",value=das_due_date(competence),key="das_due")
        amount=st.number_input("Valor do DAS",min_value=0.0,step=1.0,format="%.2f",key="das_amount")
        status=st.selectbox("Status",["Pendente","Pago"],key="das_status")
        payment_date=None
        if status=="Pago":
            payment_date=st.date_input("Data de pagamento",value=date.today(),key="das_payment_date")
        guide=st.file_uploader(
            "Anexar guia oficial (PDF)",
            type=["pdf"],
            key="das_guide_upload",
            help="Opcional. O arquivo ficará armazenado junto aos demais documentos do Razync.",
        )
        if guide is not None:
            guide_analysis = analyze_das_guide(guide.getvalue(), guide.name)
            st.markdown("**Leitura assistida da guia**")
            ga1, ga2, ga3 = st.columns(3)
            ga1.metric("Competência", guide_analysis["competence"] or "Não encontrada")
            ga2.metric("Valor provável", brl(guide_analysis["amount"]) if guide_analysis["amount"] is not None else "Não encontrado")
            ga3.metric("Confiança", guide_analysis["confidence"])
            if guide_analysis["competence"] and guide_analysis["competence"] != competence:
                st.warning("A competência identificada no PDF é diferente da competência selecionada. Confira antes de salvar.")
            for guide_warning in guide_analysis["warnings"]:
                st.info(guide_warning)
            st.caption("A leitura é apenas uma sugestão local. Valor, competência e pagamento só são gravados após sua confirmação.")
        notes=st.text_area("Observações",key="das_notes")
        if st.button("Salvar controle do DAS",type="primary",width="stretch"):
            if amount <= 0:
                st.warning("Informe o valor exibido na guia oficial.")
            else:
                try:
                    upsert_das(uid,competence,due,amount,status,payment_date,notes)
                    if guide is not None:
                        save_uploaded_document(user,guide,"DAS",competence)
                except Exception:
                    st.error("Não foi possível salvar o controle do DAS agora.")
                else:
                    st.success("DAS registrado no Razync.")
                    st.rerun()

    st.info("O vencimento sugerido considera o dia 20 do mês seguinte com ajuste básico para fim de semana. Sempre prevalecem a data e o valor impressos na guia oficial.")
    current=[d for d in das_rows if str(d["competence"]).startswith(str(year))]
    section("Competências do ano")
    if not current:
        empty_state("Nenhum DAS controlado neste ano", "Gere a guia no PGMEI e registre a competência para acompanhar vencimento e pagamento.", "▣")
    else:
        das_view=[]
        for d in current:
            das_view.append({"Competência":d["competence"],"Vencimento":d["due_date"],"Valor":d["amount"],"Status":das_status(d["status"],d["due_date"]),"Pagamento":d["payment_date"]})
        st.dataframe(pd.DataFrame(das_view),width="stretch",hide_index=True,column_config={"Valor":st.column_config.NumberColumn(format="R$ %.2f"),"Vencimento":st.column_config.DateColumn(format="DD/MM/YYYY"),"Pagamento":st.column_config.DateColumn(format="DD/MM/YYYY")})

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
        st.dataframe(obd,width="stretch",hide_index=True,column_config={"Vencimento":st.column_config.DateColumn(format="DD/MM/YYYY")})
    else:
        empty_state("Nenhuma obrigação para exibir", "Quando houver tarefas automáticas ou personalizadas, elas aparecerão aqui organizadas por vencimento.", "✓")
    with st.expander("Adicionar obrigação personalizada"):
        with st.form("obl_form",clear_on_submit=True):
            title=st.text_input("Título"); due=st.date_input("Vencimento",value=date.today()); cat=st.selectbox("Categoria",["Fiscal","Financeira","Administrativa","Trabalhista","Outra"]); notes=st.text_area("Observações")
            if st.form_submit_button("Adicionar",width="stretch"):
                if title.strip(): add_obligation(uid,title=title.strip(),due_date=due,status="Pendente",category=cat,notes=notes.strip()); st.rerun()
    if manual:
        with st.expander("Atualizar tarefas personalizadas"):
            item=st.selectbox("Tarefa",[o["id"] for o in manual],format_func=lambda x:next(o["title"] for o in manual if o["id"]==x))
            status=st.selectbox("Novo status",["Pendente","Concluído"],key="oblstatus")
            c1,c2=st.columns(2)
            if c1.button("Atualizar",width="stretch"): update_obligation_status(uid,int(item),status); st.rerun()
            if c2.button("Excluir",width="stretch"): delete_obligation(uid,int(item)); st.rerun()

elif page == "Clientes e Fornecedores":
    header("Clientes e Fornecedores","Mantenha os contatos essenciais organizados para reutilizar em vendas, compras e documentos.")
    with st.container(border=True):
        st.caption("NOVO CONTATO")
        with st.form("contact_form",clear_on_submit=True):
            a,b=st.columns([1,2]); typ=a.segmented_control("Tipo",["Cliente","Fornecedor"],default="Cliente",selection_mode="single") or "Cliente"; name=b.text_input("Nome",placeholder="Nome ou razão social")
            with st.expander("Mais detalhes (opcional)"):
                a,b,c=st.columns(3); doc=a.text_input("CPF/CNPJ"); email=b.text_input("E-mail"); phone=c.text_input("Telefone")
                notes=st.text_area("Observações")
            save=st.form_submit_button("Salvar contato",type="primary",width="stretch")
            if save:
                document_ok, document_error = cpf_or_cnpj_status(doc)
                if not name.strip():
                    st.error("Informe o nome do contato.")
                elif not document_ok:
                    st.error(document_error)
                else:
                    add_contact(uid,contact_type=typ,name=name.strip(),document=doc.strip(),email=email.strip(),phone=phone.strip(),notes=notes.strip())
                    st.rerun()
    section("Contatos")
    if not contacts:
        empty_state("Nenhum cliente ou fornecedor", "Adicione seu primeiro contato para organizar quem compra de você e de quem sua empresa compra.", "◇")
    else:
        cdf=pd.DataFrame(contacts); st.dataframe(cdf,width="stretch",hide_index=True)
        with st.expander("Excluir contato"):
            cid=st.selectbox("Selecione",[c["id"] for c in contacts],format_func=lambda x:next(c["name"] for c in contacts if c["id"]==x),key="delcontact"); st.caption("A exclusão é definitiva.")
            if st.button("Excluir contato selecionado",width="stretch"): delete_contact(uid,int(cid)); st.rerun()

elif page == "Empregado":
    header("Empregado","Organize informações básicas quando o MEI possuir empregado registrado.")
    with st.container(border=True):
        st.caption("CADASTRO DO EMPREGADO")
        with st.form("emp_form",clear_on_submit=True):
            name=st.text_input("Nome",placeholder="Nome completo")
            a,b=st.columns(2); admission=a.date_input("Data de admissão",value=date.today()); salary=b.number_input("Salário",min_value=0.0,step=50.0)
            with st.expander("Mais detalhes (opcional)"):
                cpf=st.text_input("CPF"); status=st.selectbox("Status",["Ativo","Inativo"]); notes=st.text_area("Observações")
            save=st.form_submit_button("Salvar empregado",type="primary",width="stretch")
            if save:
                if not name.strip():
                    st.error("Informe o nome do empregado.")
                elif cpf.strip() and not valid_cpf(cpf):
                    st.error("CPF inválido.")
                else:
                    add_employee(uid,name=name.strip(),cpf=cpf.strip(),admission_date=admission,salary=salary,status=status,notes=notes.strip())
                    st.rerun()
    section("Empregados cadastrados")
    if not employees:
        empty_state("Nenhum empregado cadastrado", "Se o seu MEI possuir empregado, registre os dados básicos aqui para manter essa informação junto da gestão do negócio.", "♙")
    else:
        st.dataframe(pd.DataFrame(employees),width="stretch",hide_index=True)
        with st.expander("Excluir empregado"):
            eid=st.selectbox("Selecione",[e["id"] for e in employees],format_func=lambda x:next(e["name"] for e in employees if e["id"]==x),key="delemp"); st.caption("A exclusão é definitiva.")
            if st.button("Excluir empregado selecionado",width="stretch"): delete_employee(uid,int(eid)); st.rerun()

elif page == "Documentos":
    header("Documentos","Guarde comprovantes, notas e arquivos por competência. O Razync lê PDFs com texto e sugere a organização para você confirmar.")
    with st.container(border=True):
        st.caption("ADICIONAR DOCUMENTO")
        up=st.file_uploader(
            "Escolha um arquivo",
            type=["pdf","png","jpg","jpeg"],
            key="docup",
            help="A análise acontece no próprio aplicativo. Nenhum arquivo é enviado a serviços externos.",
        )
        suggestion = None
        if up is not None:
            suggestion = analyze_document(up.getvalue(), up.type or "", up.name)
            st.markdown("**Sugestões encontradas**")
            s1,s2,s3=st.columns(3)
            s1.metric("Tipo", suggestion["category"])
            s2.metric("Competência", suggestion["reference_month"] or "Não encontrada")
            s3.metric("Confiança", suggestion["confidence"])
            details = []
            if suggestion["value"] is not None:
                details.append(f"valor provável: {brl(suggestion['value'])}")
            if suggestion["document_number"]:
                details.append(f"identificador: {suggestion['document_number']}")
            if details:
                st.caption(" • ".join(details))
            if suggestion["warning"]:
                st.info(suggestion["warning"])
            if suggestion["text_preview"]:
                with st.expander("Ver trecho reconhecido"):
                    st.text(suggestion["text_preview"])
            st.caption("Revise as sugestões antes de salvar; o Razync não altera seus lançamentos automaticamente.")

        suggested_category = suggestion["category"] if suggestion else "Nota Fiscal"
        suggested_reference = suggestion["reference_month"] if suggestion else ""
        a,b=st.columns(2)
        category=a.selectbox(
            "Tipo de documento",
            DOCUMENT_CATEGORIES,
            index=DOCUMENT_CATEGORIES.index(suggested_category),
            key=f"doc_category_{up.name if up else 'empty'}",
        )
        reference=b.text_input(
            "Competência",
            value=suggested_reference,
            placeholder="AAAA-MM",
            key=f"doc_reference_{up.name if up else 'empty'}",
        )
        valid_reference = not reference.strip() or valid_competence(reference.strip())
        if not valid_reference:
            st.warning("Use o formato AAAA-MM para a competência, por exemplo 2026-08.")
        if st.button("Salvar documento",type="primary",width="stretch",disabled=up is None or not valid_reference):
            if up:
                try:
                    save_uploaded_document(user, up, category, reference.strip())
                except Exception:
                    st.error("Não foi possível armazenar o documento agora.")
                else:
                    st.success("Documento salvo com segurança.")
                    st.rerun()
    section("Arquivos salvos")
    if not docs:
        empty_state("Nenhum documento salvo", "Adicione comprovantes, notas e extratos. Eles ficam organizados por tipo e competência para facilitar os fechamentos.", "▱")
    else:
        ddf=pd.DataFrame(docs)
        visible_columns=[column for column in ["filename","category","reference_month","created_at"] if column in ddf.columns]
        st.dataframe(ddf[visible_columns],width="stretch",hide_index=True)
        did=st.selectbox("Abrir documento",[d["id"] for d in docs],format_func=lambda x:next(d["filename"] for d in docs if d["id"]==x))
        selected_meta = next(d for d in docs if int(d["id"]) == int(did))
        prepared_key = f"_prepared_document_{uid}_{int(did)}"
        if st.button("Preparar arquivo para download", key=f"prepare_doc_{did}", width="stretch"):
            try:
                selected = get_document(uid,int(did))
                if not selected:
                    raise RuntimeError("Documento não encontrado")
                content = document_bytes(selected)
            except Exception:
                st.error("Não foi possível baixar o documento agora.")
            else:
                st.session_state[prepared_key] = {
                    "content": content,
                    "filename": selected["filename"],
                    "mime_type": selected["mime_type"] or "application/octet-stream",
                }
        prepared_document = st.session_state.get(prepared_key)
        if prepared_document:
            st.download_button(
                "Baixar arquivo",
                prepared_document["content"],
                file_name=prepared_document["filename"],
                mime=prepared_document["mime_type"],
                width="stretch",
            )
        with st.expander("Excluir documento"):
            st.caption("A exclusão remove o arquivo armazenado no Razync.")
            if st.button("Excluir documento selecionado",width="stretch"):
                try:
                    remove_saved_document(uid, selected_meta)
                except Exception:
                    st.error("Não foi possível excluir o documento agora.")
                else:
                    st.session_state.pop(prepared_key, None)
                    st.rerun()
        st.subheader("Cobertura documental")
        coverage=document_coverage(docs,CURRENT_YEAR); st.dataframe(coverage,width="stretch",hide_index=True)

elif page == "Espaço do Contador":
    header("Espaço do Contador", "Prepare um pacote organizado para compartilhar sem liberar sua senha.")
    st.warning("Nunca compartilhe senha do gov.br, banco ou Razync. Envie apenas os relatórios e arquivos necessários.")
    accountant_year = st.selectbox("Ano de referência", list(range(CURRENT_YEAR - 4, CURRENT_YEAR + 1)), index=4, key="accountant_year")
    accountant_month = st.selectbox("Mês de referência", list(range(1, 13)), index=date.today().month - 1, format_func=lambda value: MONTH_NAMES_PT[value - 1], key="accountant_month")
    summary_pdf = financial_summary_pdf(profile, accountant_year, financial_analysis(transactions, accountant_year))
    accountant_closing = monthly_closing(transactions, invoices, docs, das_rows, accountant_year, accountant_month)
    closing_pdf = closing_summary_pdf(profile, accountant_year, accountant_month, accountant_closing)
    p1, p2 = st.columns(2)
    p1.download_button("Resumo financeiro", summary_pdf, file_name=f"resumo_contador_{accountant_year}.pdf", mime="application/pdf", width="stretch")
    p2.download_button("Fechamento do mês", closing_pdf, file_name=f"fechamento_{accountant_year}_{accountant_month:02d}.pdf", mime="application/pdf", width="stretch")
    st.caption("Para documentos e dados completos, gere também o backup e compartilhe o arquivo por um canal seguro.")
    if st.button("Preparar backup completo", width="stretch"):
        st.session_state["_navigate_to"] = "Backup"
        st.rerun()

elif page == "Central de Automações":
    header("Central de Automações", "O Razync revisa seus dados, antecipa pendências e prepara as próximas ações sem alterar nada sem sua confirmação.")
    automation = automation_overview(
        profile, transactions, invoices, das_rows, obligations, docs,
        CURRENT_YEAR, date.today().month,
    )
    closing = automation["closing"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fechamento do mês", f"{closing['score']}%")
    c2.metric("Conciliações sugeridas", len(automation["invoice_matches"]))
    c3.metric("DAS identificados", len(automation["das_matches"]))
    c4.metric("Sem documento", automation["documents"]["missing_count"])

    section("Resumo automático de hoje", "Prioridades explicadas e com acesso direto ao local certo.")
    for idx, item in enumerate(automation["action_items"][:6]):
        action_text, action_button = st.columns([4.7, 1.2])
        with action_text:
            level = "danger" if item["priority"] == 1 else "warn" if item["priority"] == 2 else "info" if item["priority"] == 3 else "ok"
            alert_card(level, item["title"], item["detail"])
        with action_button:
            if item["page"] and st.button("Abrir", key=f"automation_action_{idx}", width="stretch"):
                st.session_state["_navigate_to"] = item["page"]
                st.rerun()

    today_tab, closing_tab, review_tab, forecast_tab, share_tab = st.tabs([
        "Hoje", "Fechamento", "Conciliação", "Previsão", "Cobranças e contador"
    ])

    with today_tab:
        st.subheader("12 rotinas disponíveis")
        routines = [
            ("Fechamento mensal", "Automática", "Revisa movimentações, notas, documentos e DAS."),
            ("Conciliação", "Assistida", "Sugere vínculos e aguarda sua confirmação."),
            ("Categorias inteligentes", "Automática", "Reutiliza suas próprias classificações anteriores."),
            ("DAS", "Assistida", "Localiza possíveis pagamentos no extrato."),
            ("Documentos", "Automática", "Lê PDFs e sugere tipo, competência e valor."),
            ("NFS-e", "Assistida", "Importa arquivos e bloqueia números já cadastrados."),
            ("Previsão financeira", "Automática", "Projeta os próximos três meses."),
            ("Alertas inteligentes", "Automática", "Mostra somente situações que exigem atenção."),
            ("Pacote do contador", "Assistida", "Prepara relatório e backup sem compartilhar senhas."),
            ("Backup", "Assistida", "Gera um pacote completo sob demanda."),
            ("Cobrança de clientes", "Assistida", "Prepara lembretes; você decide se envia."),
            ("Assistente proativo", "Automática", "Apresenta as prioridades no painel."),
        ]
        st.dataframe(pd.DataFrame(routines, columns=["Rotina", "Modo", "O que faz"]), width="stretch", hide_index=True)
        q1, q2, q3 = st.columns(3)
        if q1.button("Importar NFS-e", width="stretch"):
            st.session_state["_navigate_to"] = "Importar NFS-e"; st.rerun()
        if q2.button("Organizar documentos", width="stretch"):
            st.session_state["_navigate_to"] = "Documentos"; st.rerun()
        if q3.button("Ver alertas", width="stretch"):
            st.session_state["_navigate_to"] = "Central de Notificações"; st.rerun()

    with closing_tab:
        st.progress(closing["score"] / 100)
        st.caption(f"Fechamento de {date.today().month:02d}/{CURRENT_YEAR}: {closing['score']}% pronto")
        checklist = pd.DataFrame(closing["checklist"])
        st.dataframe(checklist, width="stretch", hide_index=True)
        if st.button("Abrir fechamento mensal", key="automation_closing", width="stretch"):
            st.session_state["_navigate_to"] = "Fechamento Mensal"; st.rerun()

    with review_tab:
        st.subheader("Possíveis pagamentos de DAS")
        if automation["das_matches"]:
            st.dataframe(pd.DataFrame(automation["das_matches"]), width="stretch", hide_index=True)
            st.caption("O Razync apenas sugere. Confirme o pagamento na página DAS depois de conferir o extrato.")
        else:
            st.success("Nenhum possível pagamento de DAS aguardando revisão.")
        st.subheader("Despesas fora do padrão")
        if automation["anomalies"]:
            anomaly_df = pd.DataFrame(automation["anomalies"]).rename(columns={"description": "Descrição", "category": "Categoria", "value": "Valor", "reference": "Mediana"})
            st.dataframe(anomaly_df, width="stretch", hide_index=True, column_config={"Valor": st.column_config.NumberColumn(format="R$ %.2f"), "Mediana": st.column_config.NumberColumn(format="R$ %.2f")})
        else:
            st.success("Nenhuma despesa fora do padrão foi identificada.")
        if st.button("Abrir conciliação inteligente", key="automation_reconcile", width="stretch"):
            st.session_state["_navigate_to"] = "Conciliação"; st.rerun()

    with forecast_tab:
        st.caption("Projeção baseada na média dos últimos três meses cadastrados.")
        st.dataframe(
            automation["forecast"], width="stretch", hide_index=True,
            column_config={
                "Receitas previstas": st.column_config.NumberColumn(format="R$ %.2f"),
                "Despesas previstas": st.column_config.NumberColumn(format="R$ %.2f"),
                "Saldo projetado": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )
        projected = automation["forecast"]
        if not projected.empty and float(projected.iloc[-1]["Saldo projetado"]) < 0:
            st.error("A projeção indica saldo negativo. Revise despesas e recebimentos previstos.")
        else:
            st.success("A projeção atual não indica saldo negativo nos próximos três meses.")

    with share_tab:
        st.subheader("Lembretes de recebimento")
        reminders = automation["reminders"]
        if not reminders:
            st.success("Nenhuma nota emitida está aguardando conciliação com recebimento.")
        else:
            reminder_labels = {item["invoice_id"]: f"Nota {item['number'] or item['invoice_id']} · {item['customer']} · {brl(item['amount'])}" for item in reminders}
            reminder_id = st.selectbox("Nota para preparar lembrete", list(reminder_labels), format_func=lambda value: reminder_labels[value])
            reminder = next(item for item in reminders if item["invoice_id"] == reminder_id)
            st.text_area("Mensagem preparada", value=reminder["message"], height=140)
            r1, r2 = st.columns(2)
            r1.link_button("Abrir no WhatsApp", reminder["whatsapp_url"], width="stretch")
            r2.link_button("Abrir no e-mail", reminder["email_url"], width="stretch")
            st.caption("Nenhuma mensagem é enviada automaticamente. Revise antes de enviar.")
        p1, p2 = st.columns(2)
        if p1.button("Abrir Espaço do Contador", width="stretch"):
            st.session_state["_navigate_to"] = "Espaço do Contador"; st.rerun()
        if p2.button("Preparar backup", width="stretch"):
            st.session_state["_navigate_to"] = "Backup"; st.rerun()

elif page == "Assistente Razync":
    header("Assistente Razync IA", "Converse com uma IA que entende o resumo financeiro e fiscal registrado no seu Razync.")
    render_ai_assistant(
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=docs,
        annual_limit=limit,
        current_year=CURRENT_YEAR,
        fallback_answer=lambda question: assistant_answer(
            question,
            transactions,
            invoices,
            das_rows,
            limit,
            CURRENT_YEAR,
            obligations=obligations,
            documents=docs,
        ),
    )

elif page == "Primeiros Passos":
    header("Primeiros Passos", "Configure o Razync Pro para o seu MEI e deixe os alertas, limites e relatórios mais úteis.")
    progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))
    c1,c2 = st.columns([1,3])
    c1.metric("Configuração", f"{progress['percent']}%")
    with c2:
        st.caption(f"{progress['done']} de {progress['total']} etapas concluídas")
        st.progress(progress["percent"] / 100)

    next_step = next_onboarding_step(progress)
    if next_step:
        alert_card("info", f"Próxima etapa: {next_step['action']}", next_step["detail"])
        if next_step["page"] != "Primeiros Passos" and st.button(next_step["action"], key="onboarding_next_action", type="primary", width="stretch"):
            st.session_state["_navigate_to"] = next_step["page"]
            st.rerun()
    else:
        st.success("Configuração inicial concluída. O Razync já consegue gerar alertas e relatórios mais completos.")

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
        if st.form_submit_button("Salvar configuração básica", type="primary", width="stretch"):
            save_profile(uid, business_name=business_name, trade_name=business_name, cnpj=cnpj, main_activity=main_activity, activity_type=activity_type, opening_date=opening_date)
            st.rerun()

    section("2. Próximas etapas")
    progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))
    st.caption("Roteiro recomendado para os primeiros minutos no Razync.")
    for setup_item in first_session_plan(progress):
        if not setup_item["done"]:
            st.write(f"○ **{setup_item['title']}** — {setup_item['detail']}")
    step_cards = []
    for step in progress["steps"]:
        state_class = "is-done" if step["done"] else "is-pending"
        state_label = "Concluído" if step["done"] else "Pendente"
        step_cards.append(
            f'<div class="rz-status-step {state_class}"><strong>{escape(step["title"])}</strong>'
            f'<span>{state_label} · {escape(step["detail"])}</span></div>'
        )
    st.markdown('<div class="rz-status-grid">' + "".join(step_cards) + "</div>", unsafe_allow_html=True)

    a,b,c = st.columns(3)
    if a.button("Registrar movimentação", width="stretch"): st.session_state["_navigate_to"]="Movimentações"; st.rerun()
    if b.button("Configurar DAS", width="stretch"): st.session_state["_navigate_to"]="DAS"; st.rerun()
    if c.button("Adicionar documento", width="stretch"): st.session_state["_navigate_to"]="Documentos"; st.rerun()

    section("Recomendações do Razync")
    for tip in recommended_setup(profile):
        helper_note(tip)

elif page == "Meu MEI":
    header("Meu MEI","Cadastre os dados usados nos relatórios e alertas.")
    with st.form("profile_form"):
        cnpj=st.text_input("CNPJ",value=str(profile.get("cnpj") or "")); business=st.text_input("Razão social",value=str(profile.get("business_name") or "")); trade=st.text_input("Nome fantasia",value=str(profile.get("trade_name") or "")); activity=st.text_input("Atividade principal",value=str(profile.get("main_activity") or "")); activity_type=st.selectbox("Tipo de atividade",["Serviços","Comércio","Indústria","Misto"],index=["Serviços","Comércio","Indústria","Misto"].index(profile.get("activity_type") if profile.get("activity_type") in ["Serviços","Comércio","Indústria","Misto"] else "Serviços")); opening_date=st.date_input("Data de abertura",value=opening or date.today()); annual_limit=st.number_input("Limite anual personalizado (opcional)",min_value=0.0,value=float(profile.get("annual_limit") or MEI_ANNUAL_LIMIT),step=1000.0); city=st.text_input("Município",value=str(profile.get("city") or "")); state=st.text_input("UF",value=str(profile.get("state") or ""),max_chars=2); phone=st.text_input("Telefone",value=str(profile.get("phone") or "")); municipal=st.text_input("Inscrição municipal",value=str(profile.get("municipal_registration") or "")); state_reg=st.text_input("Inscrição estadual",value=str(profile.get("state_registration") or "")); has_employee=st.checkbox("Possui empregado",value=bool(profile.get("has_employee",False)))
        if st.form_submit_button("Salvar dados",width="stretch"):
            if cnpj.strip() and not valid_cnpj(cnpj):
                st.error("CNPJ inválido. Confira os 14 dígitos antes de salvar.")
            else:
                save_profile(uid,cnpj=cnpj,business_name=business,trade_name=trade,main_activity=activity,activity_type=activity_type,opening_date=opening_date,annual_limit=annual_limit,city=city,state=state.upper(),phone=phone,municipal_registration=municipal,state_registration=state_reg,has_employee=has_employee)
                st.success("Dados salvos.")
                st.rerun()

elif page == "Central de Notificações":
    header("Central de Notificações", "Priorize vencimentos, resolva no local certo e leve os prazos para o calendário.")
    notification_items = build_notifications(das_rows, obligations, year_revenue, limit)
    if not notification_items:
        st.success("Nenhum alerta importante identificado agora.")
    else:
        for idx, item in enumerate(notification_items):
            level = "danger" if item["level"] == "urgent" else "warn"
            if st.button(
                f"**{item['title']}**\n\n{item['detail']}\n\nResolver agora →",
                key=f"rz_action_card_{level}_notification_{idx}",
                width="stretch",
            ):
                st.session_state["_navigate_to"] = item["page"]
                st.rerun()
        calendar_file = notification_calendar(notification_items, "https://razync-pro-je8appbtpfqcrg33nn6u5r8.streamlit.app/")
        st.download_button("Adicionar prazos ao calendário (.ics)", calendar_file, file_name="agenda_razync_mei.ics", mime="text/calendar", width="stretch")
    st.caption("Os alertas são calculados com os dados cadastrados. Confirme sempre datas e valores nos documentos oficiais.")

elif page == "Integrações":
    header("Integrações", "Veja o que já funciona, o que exige confirmação e o que depende de credenciais externas.")
    runtime = database_runtime_info()
    integration_config = {
        key: secret_value(key)
        for key in (
            "SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "CHECKOUT_PRO_URL",
            "OPEN_FINANCE_PROVIDER_URL", "WHATSAPP_BUSINESS_URL",
        )
    }
    catalog = integration_catalog(integration_config, runtime["persistent"])
    active_count = sum(1 for item in catalog if item["ready"])
    automatic_count = sum(1 for item in catalog if item["mode"] == "Automático")
    i1, i2, i3 = st.columns(3)
    i1.metric("Disponíveis", f"{active_count}/{len(catalog)}")
    i2.metric("Automáticas", automatic_count)
    i3.metric("Sempre com confirmação", len(catalog) - automatic_count)

    section("Central de conexões", "Nenhuma integração envia dados ou mensagens sem autorização.")
    left, right = st.columns(2, gap="large")
    for idx, item in enumerate(catalog):
        target = left if idx % 2 == 0 else right
        with target:
            with st.container(border=True):
                st.markdown(f"**{item['name']}**")
                st.caption(f"{integration_maturity(item)} · {item['mode']} · {item['status']}")
                st.write(item["detail"])
                if item["page"] and st.button("Abrir recurso", key=f"integration_page_{idx}", width="stretch"):
                    st.session_state["_navigate_to"] = item["page"]
                    st.rerun()
                if item["name"] == "DAS do MEI":
                    st.link_button("Abrir portal oficial", OFFICIAL_SERVICES["das"]["url"], width="stretch")
                elif item["name"] == "NFS-e Nacional":
                    st.link_button("Abrir emissor oficial", OFFICIAL_SERVICES["nfse"]["url"], width="stretch")

    st.info("Open Finance direto exige um provedor participante e consentimento do cliente. WhatsApp automático exige conta Business e aprovação do provedor. Até lá, importação de extrato e mensagens revisadas continuam disponíveis.")

elif page == "Plano e Assinatura":
    header("Plano e Assinatura", "Acompanhe os recursos disponíveis e, quando configurado, faça o upgrade por checkout seguro.")
    if st.session_state.get("auth_provider") == "github":
        st.success("Plano atual: Razync Pro — acesso de desenvolvimento")
    else:
        st.info("Plano atual: Essencial")
    plan_name = "Pro" if st.session_state.get("auth_provider") == "github" else "Essencial"
    plan = PLAN_CATALOG[plan_name]
    st.caption(plan["description"])
    for feature in plan["features"]:
        st.write(f"✓ {feature}")
    st.caption("Preços não ficam fixos no código; o checkout comercial é configurado por ambiente.")
    config = {"CHECKOUT_PRO_URL": secret_value("CHECKOUT_PRO_URL")}
    payment_url = checkout_url(config, "pro")
    if payment_url:
        st.link_button("Assinar Razync Pro", payment_url, type="primary", width="stretch")
        st.caption("O pagamento é processado pelo provedor configurado; dados de cartão não passam pelo Razync.")
    else:
        st.caption("Checkout comercial ainda não configurado. O uso atual permanece inalterado.")

elif page == "Segurança da Conta":
    header("Segurança da Conta", "Atualize sua senha e confira como sua sessão é protegida.")
    if st.session_state.get("auth_provider") == "github":
        st.success(
            f"Acesso de desenvolvedor conectado com GitHub: @{st.session_state.get('github_login', '')}."
        )
        st.info("A segurança e a senha deste acesso são administradas diretamente pelo GitHub.")
    else:
        with st.container(border=True):
            st.subheader("Alterar senha")
            with st.form("change_password_form", clear_on_submit=True):
                new_password = st.text_input("Nova senha", type="password", help="Use pelo menos 8 caracteres.")
                password_confirmation = st.text_input("Confirmar nova senha", type="password")
                change_password = st.form_submit_button("Alterar senha", type="primary", width="stretch")
            if change_password:
                if new_password != password_confirmation:
                    st.error("As senhas não coincidem.")
                elif len(new_password) < 8:
                    st.error("A nova senha deve ter pelo menos 8 caracteres.")
                elif not is_supabase_auth_configured():
                    st.error("A alteração de senha requer o Supabase Auth.")
                else:
                    try:
                        supabase_update_password(st.session_state.get("access_token", ""), st.session_state.get("refresh_token", ""), new_password)
                    except AuthServiceError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Senha alterada com sucesso.")
    section("Verificação de segurança")
    runtime = database_runtime_info()
    storage_ready = bool(secret_value("SUPABASE_URL") and secret_value("SUPABASE_PUBLISHABLE_KEY"))
    leaked_passwords_ready = secret_value("LEAKED_PASSWORD_PROTECTION_ENABLED").lower() in {"1", "true", "yes", "sim"}
    checks = security_checklist(
        auth_enabled=is_supabase_auth_configured() or st.session_state.get("auth_provider") == "github",
        database_persistent=runtime["persistent"],
        storage_enabled=storage_ready,
        leaked_password_protection=leaked_passwords_ready,
    )
    security_cards = []
    for check in checks:
        state_class = "is-done" if check["done"] else "is-pending"
        state_label = "Ativo" if check["done"] else "Revisar"
        security_cards.append(
            f'<div class="rz-status-step {state_class}"><strong>{escape(check["title"])}</strong>'
            f'<span>{state_label} · {escape(check["detail"])}</span></div>'
        )
    st.markdown('<div class="rz-status-grid">' + "".join(security_cards) + "</div>", unsafe_allow_html=True)
    if not leaked_passwords_ready:
        st.link_button(
            "Como ativar proteção contra senhas vazadas",
            "https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection",
            width="stretch",
        )

    section("Sessão e privacidade")
    st.write("✓ A opção **Manter conectado** armazena somente um token de renovação criptografado.")
    st.write("✓ Ao sair, a sessão local e o token persistente são removidos.")
    st.write("✓ Os dados de cada conta são isolados pelo usuário autenticado.")
    st.info("Em dispositivo compartilhado, use sempre o botão Sair ao terminar.")

elif page == "Histórico de Atividades":
    header("Histórico de Atividades","Consulte alterações registradas automaticamente nos seus dados do Razync.")
    audit_rows=list_audit_logs(uid,250)
    if not audit_rows:
        empty_state("Nenhuma atividade registrada", "As próximas inclusões, alterações e exclusões aparecerão aqui.", "◷")
    else:
        action_labels={"INSERT":"Criado","UPDATE":"Alterado","DELETE":"Excluído"}
        module_labels={"transactions":"Movimentações","das_items":"DAS","documents":"Documentos","invoices":"Notas fiscais","contacts":"Contatos","employees":"Empregado","obligations":"Obrigações","recurring_transactions":"Recorrências","mei_profiles":"Meu MEI"}
        audit_view=pd.DataFrame([{
            "Data":row.get("created_at"),
            "Módulo":module_labels.get(row.get("table_name"),row.get("table_name")),
            "Ação":action_labels.get(row.get("action"),row.get("action")),
            "Registro":row.get("record_id") or "—",
        } for row in audit_rows])
        filter_module=st.selectbox("Filtrar módulo",["Todos"]+sorted(audit_view["Módulo"].dropna().unique().tolist()))
        if filter_module!="Todos": audit_view=audit_view[audit_view["Módulo"]==filter_module]
        st.dataframe(audit_view,width="stretch",hide_index=True,column_config={"Data":st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")})
        st.caption("Por segurança, senhas e conteúdo binário de documentos nunca são incluídos no histórico.")

elif page == "Status do Sistema":
    header("Status do Sistema","Veja se o Razync está usando uma infraestrutura adequada para produção.")
    runtime=database_runtime_info()
    c1,c2,c3=st.columns(3)
    c1.metric("Banco",runtime["backend"]); c2.metric("Persistência","Ativa" if runtime["persistent"] else "Temporária"); c3.metric("Produção","Pronto" if runtime["production_ready"] else "Configuração necessária")
    if runtime["persistent"]: st.success("O banco configurado é persistente.")
    else: st.warning("O app está usando SQLite temporário. No Streamlit Cloud, configure DATABASE_URL com PostgreSQL/Supabase antes de colocar clientes reais.")
    st.subheader("Integrações")
    status_config = {key: secret_value(key) for key in ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "CHECKOUT_PRO_URL")}
    for integration in integration_readiness(status_config, runtime["persistent"]):
        marker = "✓" if integration["ready"] else "○"
        st.write(f"{marker} **{integration['name']}** — {integration['detail']}")
    st.write("○ **Integrações bancárias diretas** — importação inteligente de arquivo já disponível")
    section("Prontidão de produção")
    readiness = production_checklist(
        persistent_db=runtime["persistent"],
        auth_ready=is_supabase_auth_configured(),
        storage_ready=bool(secret_value("SUPABASE_URL") and secret_value("SUPABASE_PUBLISHABLE_KEY")),
        session_secret=bool(secret_value("SESSION_COOKIE_SECRET")),
    )
    for check in readiness:
        marker = "✓" if check["ok"] else "○"
        st.write(f"{marker} **{check['item']}** — {check['detail']}")

elif page == "Backup":
    header("Backup","Baixe um pacote dos dados para manter uma cópia independente.")
    backup_key = f"_prepared_backup_{uid}_{_current_data_version}"
    st.caption("O backup é preparado somente quando você solicitar, evitando carregar todos os documentos ao abrir esta página.")
    if st.button("Preparar backup completo", type="primary", width="stretch"):
        with st.spinner("Preparando backup..."):
            backup = build_backup_zip(
                profile, transactions, invoices, das_rows, obligations, contacts, employees, docs,
                lambda doc_id:(lambda d: {**d, "content": document_bytes(d)} if d else None)(get_document(uid,doc_id)),
            )
            st.session_state[backup_key] = backup
    backup = st.session_state.get(backup_key)
    if backup:
        st.download_button("Baixar backup completo (.zip)",backup,file_name=f"backup_razync_{date.today().isoformat()}.zip",mime="application/zip",width="stretch")
        st.caption("O pacote inclui dados em CSV/JSON, manifesto e os documentos disponíveis no Razync Pro.")
        st.code(backup_checksum(backup), language=None)
        st.caption("Guarde este código de integridade junto do arquivo para conferir se o backup não foi alterado.")

st.divider()
st.caption("Razync Pro • Ecossistema Razync • ferramenta de organização contábil e financeira para MEI")
