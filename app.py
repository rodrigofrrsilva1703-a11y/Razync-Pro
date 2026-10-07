from __future__ import annotations

from datetime import date
from html import escape
import os

import pandas as pd
import streamlit as st

from database import (
    add_contact, add_employee, add_invoice, add_obligation, add_transaction,
    delete_contact, delete_document, delete_employee,
    delete_invoice, delete_obligation, delete_transaction, get_document, get_profile,
    init_db, list_contacts, list_das, list_documents, list_employees, list_invoices,
    list_obligations, list_transactions, save_document, save_profile,
    update_contact, update_employee, update_invoice, update_obligation_status, update_transaction, upsert_das, link_transaction_document,
    dashboard_financial_summary, transaction_document_numbers, count_transactions, list_transactions_page,
    load_user_snapshot, data_version, DatabaseConnectionError, resolve_public_workspace_user, add_recurring_transaction, delete_recurring_transaction, list_recurring_transactions,
    materialize_due_recurring, set_recurring_transaction_active, list_audit_logs, add_transactions_bulk,
)
from database import database_runtime_info
from fiscal_rules import (
    MEI_ANNUAL_LIMIT, annual_limit_for, build_alerts, competence_list,
    das_due_date, das_status,
)
from mei_obligations import automatic_obligations, upcoming_automatic_obligations
from business_tools import monthly_closing, financial_analysis, consistency_checks
from product_core import NAV_GROUPS, group_for_page, action_items, reconciliation_summary, assistant_answer
from backup_tools import backup_checksum, build_backup_zip, document_coverage
from onboarding_tools import onboarding_progress, recommended_setup, first_session_plan
from reconciliation_tools import smart_invoice_matches, duplicate_groups
from automation_tools import financial_projection, upcoming_deadlines
from ui_system import inject_design_system, page_header, section, alert_card, empty_state, helper_note, apply_plot_theme, tokens
from ui_helpers import MONTH_NAMES_PT, filter_transactions, paginate_frame
from growth_tools import (
    build_notifications, checkout_url, integration_readiness, normalize_nfse,
    notification_calendar, read_nfse_export, suggest_nfse_columns,
)
from automation_suite import (
    automation_overview, das_payment_matches, learned_category,
)
from brand_assets import brand_logo_data_uri, ensure_brand_assets
from customer_experience import (
    OFFICIAL_SERVICES, build_today_plan, das_journey, financial_story,
    integration_catalog, next_onboarding_step,
    transaction_restore_payload,
)
from navigation_config import SIDEBAR_LABELS, SIDEBAR_GROUPS, SIDEBAR_SECONDARY_GROUPS, SIDEBAR_ICONS
from finance_workspace import render_finance_workspace
from fiscal_workspace import render_fiscal_workspace
from workspace_style import inject_workspace_style
from compact_cards import inject_compact_cards, stat_card
from table_ui import professional_table
from dashboard_workspace import render_dashboard_workspace
from sidebar_workspace import render_sidebar
from productivity_workspace import render_productivity_workspace
from account_workspace import render_account_workspace
from validators import valid_cnpj, valid_cpf, cpf_or_cnpj_status, valid_competence
from commercial_readiness import PLAN_CATALOG, integration_maturity, production_checklist
from monitoring import safe_error, safe_event

CURRENT_YEAR = date.today().year
BRAND_LOGO_PATH = ensure_brand_assets()
BRAND_LOGO_DATA_URI = brand_logo_data_uri()

DOCUMENT_CATEGORIES = ("Nota Fiscal", "Comprovante", "Extrato Bancário", "DAS", "Contrato", "Outro")


@st.cache_data(show_spinner=False, max_entries=16)
def cached_document_analysis(content: bytes, mime_type: str, filename: str) -> dict:
    from document_intelligence import analyze_document
    return analyze_document(content, mime_type, filename)


@st.cache_data(show_spinner=False, max_entries=12)
def cached_das_guide_analysis(content: bytes, filename: str) -> dict:
    from fiscal_automation import analyze_das_guide
    return analyze_das_guide(content, filename)


@st.cache_data(show_spinner=False, ttl=600)
def cached_monthly_report_pdf(profile_data: dict, year: int, rows: list[dict]) -> bytes:
    from reports import monthly_report_pdf
    return monthly_report_pdf(profile_data, year, rows)


@st.cache_data(show_spinner=False, ttl=600)
def cached_dasn_summary_pdf(profile_data: dict, year: int, services: float, sales: float, employee: bool) -> bytes:
    from reports import dasn_summary_pdf
    return dasn_summary_pdf(profile_data, year, services, sales, employee)


@st.cache_data(show_spinner=False, ttl=600)
def cached_financial_summary_pdf(profile_data: dict, year: int, analysis: dict) -> bytes:
    from reports import financial_summary_pdf
    return financial_summary_pdf(profile_data, year, analysis)


@st.cache_data(show_spinner=False, ttl=600)
def cached_closing_summary_pdf(profile_data: dict, year: int, month: int, closing: dict) -> bytes:
    from reports import closing_summary_pdf
    return closing_summary_pdf(profile_data, year, month, closing)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_statement_frame(content: bytes, filename: str) -> pd.DataFrame:
    from io import BytesIO
    from bank_import import read_statement

    uploaded = BytesIO(content)
    uploaded.name = filename
    return read_statement(uploaded)


@st.cache_data(show_spinner=False, ttl=120, max_entries=16)
def cached_reconciliation(transactions_data: pd.DataFrame, invoices_data: pd.DataFrame):
    return (
        reconciliation_summary(transactions_data, invoices_data),
        smart_invoice_matches(transactions_data, invoices_data),
        duplicate_groups(transactions_data),
    )


st.set_page_config(page_title="Razync Pro", page_icon=BRAND_LOGO_PATH, layout="wide", initial_sidebar_state="expanded")
try:
    init_db()
    _runtime_info = database_runtime_info()
    safe_event(
        "database_runtime",
        backend=_runtime_info.get("backend"),
        status="persistent" if _runtime_info.get("persistent") else "temporary",
        environment="railway" if os.getenv("RAILWAY_PROJECT_ID") else "local",
    )
except DatabaseConnectionError as exc:
    safe_error("database_init_failed", exc, operation="init_db", backend="database")
    st.error("Não foi possível conectar o Razync Pro ao banco definitivo.")
    st.warning(str(exc))
    st.markdown("**Confira as variáveis protegidas do Railway:**")
    st.code('SUPABASE_DB_PASSWORD\nSUPABASE_DB_HOST\nSUPABASE_DB_USER\nSUPABASE_DB_PORT', language=None)
    st.caption("O diagnóstico nunca exibe senhas. Depois de corrigir as variáveis, faça um novo deploy do serviço.")
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
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def document_bytes(document: dict) -> bytes:
    if document.get("storage_path"):
        from storage_service import download_document
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
        from storage_service import upload_document
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
        from storage_service import remove_document
        remove_document(
            st.session_state.get("access_token", ""),
            st.session_state.get("refresh_token", ""),
            document["storage_path"],
        )
    delete_document(user_id, int(document["id"]))


def ensure_login() -> dict:
    """Open the temporary public workspace directly, without authentication."""
    if "user" not in st.session_state or st.session_state.get("auth_provider") != "public":
        st.session_state["user"] = resolve_public_workspace_user()
        st.session_state["auth_provider"] = "public"
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        if st.query_params:
            st.query_params.clear()
    return st.session_state["user"]

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
    for month in range(1, 13):
        cur = (
            df[
                (df["tx_type"] == "Receita")
                & (df["tx_date"].dt.year == year)
                & (df["tx_date"].dt.month == month)
            ]
            if not df.empty else df
        )
        if cur.empty:
            services = commerce = industry = with_doc = without_doc = total = 0.0
        else:
            categories = cur["category"].fillna("").astype(str)
            service_mask = categories.isin(["Serviços", "Serviço"])
            industry_mask = categories.isin(["Indústria", "Industria", "Produtos industrializados"])
            services = float(cur.loc[service_mask, "value"].sum())
            industry = float(cur.loc[industry_mask, "value"].sum())
            total = float(cur["value"].sum())
            commerce = max(total - services - industry, 0.0)
            has_doc = cur["document_number"].fillna("").astype(str).str.strip().ne("")
            with_doc = float(cur.loc[has_doc, "value"].sum())
            without_doc = total - with_doc
        rows.append({
            "month": month,
            "month_name": MONTH_NAMES_PT[month - 1],
            "with_doc": with_doc,
            "without_doc": without_doc,
            "services": services,
            "commerce": commerce,
            "industry": industry,
            "sales": commerce + industry,
            "total": total,
        })
    return rows


def category_totals_for_dasn(df: pd.DataFrame, year: int) -> tuple[float, float]:
    if df.empty:
        return 0.0, 0.0
    cur = df[(df["tx_type"] == "Receita") & (df["tx_date"].dt.year == year)]
    services = float(cur[cur["category"].isin(["Serviços", "Serviço"])]["value"].sum())
    commerce_and_industry = float(cur["value"].sum()) - services
    return services, commerce_and_industry

def cashflow_monthly(df: pd.DataFrame, year: int) -> pd.DataFrame:
    rows = []
    for month in range(1, 13):
        cur = df[df["tx_date"].dt.year == year] if not df.empty else df
        cur = cur[cur["tx_date"].dt.month == month] if not cur.empty else cur
        entradas = float(cur[cur["tx_type"] == "Receita"]["value"].sum()) if not cur.empty else 0.0
        saidas = float(cur[cur["tx_type"] == "Despesa"]["value"].sum()) if not cur.empty else 0.0
        rows.append({"Mês": MONTH_NAMES_PT[month - 1], "Entradas": entradas, "Saídas": saidas, "Resultado": entradas-saidas})
    out = pd.DataFrame(rows)
    out["Resultado acumulado"] = out["Resultado"].cumsum()
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

# Recurring entries only need one maintenance pass per session/day.
_recurring_check_key = f"_recurring_materialized_on_{uid}"
_today_key = date.today().isoformat()
generated_recurring = 0
if st.session_state.get(_recurring_check_key) != _today_key:
    try:
        generated_recurring = materialize_due_recurring(uid)
    except DatabaseConnectionError:
        generated_recurring = 0
    except Exception as exc:
        safe_error(
            "recurring_materialize_failed",
            exc,
            operation="materialize_due_recurring",
            backend="database",
        )
        generated_recurring = 0
    finally:
        st.session_state[_recurring_check_key] = _today_key
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

# Um único padrão de densidade para todas as ferramentas do workspace.
inject_compact_cards()


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
)

undo_transaction = st.session_state.get("_undo_transaction")
if undo_transaction:
    undo_text, undo_action = st.columns([5, 1.2])
    undo_text.info(f"“{undo_transaction.get('description') or 'Lançamento'}” foi excluído. Você pode desfazer esta ação nesta sessão.")
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
    header("Início", "Seu negócio, seus números e o que realmente precisa de atenção.")
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
    header("Sistema e dados", "Preferências, integrações, histórico, backup e operação do Razync Pro.")
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
        opening_date=opening,
        theme=UI_THEME,
        brl=brl,
        navigate=navigate_to,
    )

elif page == "Movimentações":
    header("Movimentações", "Registre o que entrou e saiu sem preencher mais do que o necessário.")

    month_view = transactions[
        (transactions["tx_date"].dt.year == CURRENT_YEAR)
        & (transactions["tx_date"].dt.month == date.today().month)
    ] if not transactions.empty else transactions
    month_receita = float(month_view.loc[month_view["tx_type"] == "Receita", "value"].sum()) if not month_view.empty else 0.0
    month_despesa = float(month_view.loc[month_view["tx_type"] == "Despesa", "value"].sum()) if not month_view.empty else 0.0
    movement_result = month_receita - month_despesa

    m1, m2, m3 = st.columns(3)
    with m1:
        stat_card("Entradas", brl(month_receita), detail="mês atual")
    with m2:
        stat_card("Saídas", brl(month_despesa), detail="mês atual")
    with m3:
        stat_card(
            "Resultado",
            brl(movement_result),
            detail="mês atual",
            tone="positive" if movement_result >= 0 else "danger",
        )

    form_col, side_col = st.columns([1.75, .85], gap="large")
    with form_col:
        st.markdown("#### Novo lançamento")
        with st.form("tx_form", clear_on_submit=True):
            tx_type = st.segmented_control(
                "Tipo",
                ["Receita", "Despesa"],
                default="Receita",
                selection_mode="single",
                format_func=lambda option: "Entrada" if option == "Receita" else "Saída",
                key="tx_type_new",
                width="stretch",
            ) or "Receita"

            a, b = st.columns([1, .72])
            value = a.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
            tx_date = b.date_input("Data", value=date.today())
            desc = st.text_input(
                "Descrição",
                placeholder="Ex.: pagamento do cliente ou compra de material",
            )

            revenue_categories = ["Serviços", "Comércio", "Indústria", "Outros"]
            expense_categories = [
                "Materiais", "Aluguel", "Transporte", "Taxas", "Marketing",
                "Pró-labore/Retirada", "Serviços", "Outros",
            ]
            category_options = revenue_categories if tx_type == "Receita" else expense_categories
            activity_type = str(profile.get("activity_type") or "")
            default_revenue_category = (
                "Serviços" if activity_type == "Serviços"
                else "Comércio" if activity_type == "Comércio"
                else "Indústria" if activity_type == "Indústria"
                else "Outros"
            )
            default_category = default_revenue_category if tx_type == "Receita" else "Outros"
            category = st.selectbox(
                "Categoria",
                category_options,
                index=category_options.index(default_category),
            )

            with st.expander("Detalhes opcionais"):
                a, b = st.columns(2)
                counterparty = a.text_input("Cliente ou fornecedor")
                payment = b.selectbox(
                    "Pagamento",
                    ["PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro"],
                )
                doc = st.text_input("Nota ou documento")

            submitted = st.form_submit_button(
                "Salvar movimentação",
                type="primary",
            )
            if submitted:
                if value <= 0:
                    st.error("Informe um valor maior que zero.")
                elif not desc.strip():
                    st.error("Informe uma descrição.")
                else:
                    add_transaction(
                        uid,
                        tx_date=tx_date,
                        tx_type=tx_type,
                        description=desc.strip(),
                        category=category,
                        value=value,
                        document_number=doc.strip(),
                        counterparty=counterparty.strip(),
                        payment_method=payment,
                    )
                    st.rerun()

    with side_col:
        st.markdown("#### Em vez de digitar")
        st.caption("Se você já tem o extrato do banco, importe e revise os lançamentos de uma vez.")
        if st.button(
            "Importar extrato",
            key="movement_import_statement",
            type="primary",
            width="stretch",
        ):
            navigate_to("Importar Extrato")
        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
        st.caption("ORGANIZAÇÃO")
        st.write("• Use uma descrição curta e reconhecível.")
        st.write("• Categoria é o que alimenta relatórios.")
        st.write("• Documento e cliente são opcionais.")

    st.markdown("#### Histórico")
    if transactions.empty:
        empty_state(
            "Nenhuma movimentação registrada",
            "Sua primeira entrada ou saída aparecerá aqui.",
            "↕",
        )
    else:
        f1, f2, f3 = st.columns([1, 1, 2])
        type_filter = f1.selectbox("Tipo", ["Todos", "Receita", "Despesa"])
        category_options = ["Todas"] + sorted(
            str(x) for x in transactions["category"].dropna().unique()
        )
        category_filter = f2.selectbox("Categoria", category_options)
        search_filter = f3.text_input(
            "Buscar",
            placeholder="Descrição, cliente ou documento",
        )
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
        view = view.copy()
        view["Data"] = view["tx_date"].dt.date
        view["Tipo"] = view["tx_type"]
        view["Descrição"] = view["description"]
        view["Categoria"] = view["category"]
        view["Valor"] = view["value"]
        professional_table(
            view[["id", "Data", "Tipo", "Descrição", "Categoria", "Valor"]],
            max_visible_rows=10,
            column_config={
                "id": None,
                "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            },
        )
        st.caption(f"{total_tx} lançamento(s) encontrado(s)")

        if total_tx > 50:
            pprev, pinfo, pnext = st.columns([1, 2, 1])
            if pprev.button(
                "← Anterior",
                disabled=current_tx_page <= 1,
                width="stretch",
            ):
                st.session_state["tx_history_page"] = current_tx_page - 1
                st.rerun()
            pinfo.caption(f"Página {current_tx_page} de {max_tx_page}")
            if pnext.button(
                "Próxima →",
                disabled=current_tx_page >= max_tx_page,
                width="stretch",
            ):
                st.session_state["tx_history_page"] = current_tx_page + 1
                st.rerun()

        with st.expander("Gerenciar lançamentos"):
            edit_tab, delete_tab = st.tabs(["Editar", "Excluir"])

            with edit_tab:
                edit_id = st.selectbox(
                    "Lançamento",
                    transactions["id"].tolist(),
                    format_func=lambda x: (
                        f"#{x} · {transactions.loc[transactions['id']==x,'description'].iloc[0]}"
                    ),
                    key="edit_tx_id",
                )
                edit_row = transactions.loc[transactions["id"] == edit_id].iloc[0]
                with st.form("edit_tx_form"):
                    e1, e2 = st.columns(2)
                    edit_type = e1.selectbox(
                        "Tipo",
                        ["Receita", "Despesa"],
                        index=0 if edit_row["tx_type"] == "Receita" else 1,
                    )
                    edit_date = e2.date_input(
                        "Data",
                        value=edit_row["tx_date"].date(),
                    )
                    edit_description = st.text_input(
                        "Descrição",
                        value=str(edit_row["description"] or ""),
                    )
                    e1, e2 = st.columns(2)
                    standard_edit_categories = [
                        "Serviços", "Comércio", "Indústria", "Materiais", "Aluguel",
                        "Transporte", "Taxas", "Marketing", "Pró-labore/Retirada", "Outros",
                    ]
                    current_edit_category = str(edit_row["category"] or "Outros")
                    edit_category_options = list(
                        dict.fromkeys([current_edit_category, *standard_edit_categories])
                    )
                    edit_category = e1.selectbox(
                        "Categoria",
                        edit_category_options,
                        index=0,
                    )
                    edit_value = e2.number_input(
                        "Valor",
                        min_value=0.01,
                        value=float(edit_row["value"]),
                        step=10.0,
                    )
                    with st.expander("Detalhes"):
                        e1, e2 = st.columns(2)
                        edit_counterparty = e1.text_input(
                            "Cliente ou fornecedor",
                            value=str(edit_row["counterparty"] or ""),
                        )
                        edit_document = e2.text_input(
                            "Nota ou documento",
                            value=str(edit_row["document_number"] or ""),
                        )
                        edit_payment = st.text_input(
                            "Forma de pagamento",
                            value=str(edit_row["payment_method"] or ""),
                        )
                    save_edit = st.form_submit_button(
                        "Salvar alterações",
                        type="primary",
                    )

                if save_edit:
                    if not edit_description.strip():
                        st.error("Informe uma descrição.")
                    else:
                        update_transaction(
                            uid,
                            int(edit_id),
                            tx_date=edit_date,
                            tx_type=edit_type,
                            description=edit_description.strip(),
                            category=edit_category.strip() or "Outros",
                            value=edit_value,
                            document_number=edit_document.strip(),
                            counterparty=edit_counterparty.strip(),
                            payment_method=edit_payment.strip(),
                        )
                        st.rerun()

            with delete_tab:
                item = st.selectbox(
                    "Lançamento",
                    transactions["id"].tolist(),
                    format_func=lambda x: (
                        f"#{x} · {transactions.loc[transactions['id']==x,'description'].iloc[0]}"
                    ),
                    key="delete_tx_id",
                )
                st.caption("A exclusão é definitiva.")
                if st.button(
                    "Excluir lançamento",
                    key="delete_tx_button",
                ):
                    deleted = transactions.loc[transactions["id"] == item].iloc[0].to_dict()
                    st.session_state["_undo_transaction"] = transaction_restore_payload(deleted)
                    delete_transaction(uid, int(item))
                    st.rerun()

elif page == "Recorrências":
    header("Lançamentos Recorrentes", "Automatize receitas e despesas que se repetem sem perder o controle.")

    recurring_items = list_recurring_transactions(uid)
    active_recurring = sum(1 for item in recurring_items if item.get("active"))
    r1, r2, r3 = st.columns(3)
    r1.metric("Recorrências", len(recurring_items))
    r2.metric("Ativas", active_recurring)
    r3.metric("Pausadas", len(recurring_items) - active_recurring)

    create_col, guide_col = st.columns([1.5, .85], gap="large")
    with create_col, st.container(key="rz_panel_recurring_new"):
        st.caption("NOVA RECORRÊNCIA")
        with st.form("recurring_form", clear_on_submit=True):
            recurring_type = st.segmented_control(
                "Tipo", ["Receita", "Despesa"], default="Despesa", selection_mode="single"
            ) or "Despesa"
            a, b = st.columns(2)
            recurring_description = a.text_input("Descrição", placeholder="Ex.: aluguel, internet, mensalidade")
            recurring_value = b.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
            recurring_revenue_categories = ["Serviços", "Comércio", "Indústria", "Outros"]
            recurring_expense_categories = ["Materiais", "Aluguel", "Transporte", "Taxas", "Marketing", "Pró-labore/Retirada", "Serviços", "Outros"]
            recurring_category_options = (
                recurring_revenue_categories
                if recurring_type == "Receita"
                else recurring_expense_categories
            )
            recurring_default_category = (
                "Outros"
                if recurring_type == "Despesa" or str(profile.get("activity_type") or "") == "Misto"
                else str(profile.get("activity_type") or "Outros")
            )
            if recurring_default_category not in recurring_category_options:
                recurring_default_category = "Outros"
            a, b, c3 = st.columns(3)
            recurring_category = a.selectbox(
                "Categoria",
                recurring_category_options,
                index=recurring_category_options.index(recurring_default_category),
            )
            recurring_frequency = b.selectbox("Frequência", ["Mensal", "Semanal", "Anual"])
            recurring_payment = c3.selectbox(
                "Pagamento", ["PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro"]
            )
            a, b = st.columns(2)
            recurring_start = a.date_input("Primeira ocorrência", value=date.today())
            has_end = b.checkbox("Definir data final")
            recurring_end = b.date_input("Data final", value=date.today(), disabled=not has_end)
            save_recurring = st.form_submit_button("Salvar recorrência", type="primary", width="stretch")
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

    with guide_col, st.container(key="rz_panel_recurring_guide"):
        st.caption("COMO FUNCIONA")
        st.markdown("**O Razync gera a ocorrência quando a data chega.**")
        st.caption("Você pode pausar ou excluir a regra a qualquer momento.")
        st.markdown(
            '<div class="rz-inline-meta"><span>Mensal</span><span>Semanal</span><span>Anual</span></div>',
            unsafe_allow_html=True,
        )

    section("Recorrências cadastradas", "Pause, reative ou exclua quando precisar.")
    if not recurring_items:
        empty_state(
            "Nenhuma recorrência cadastrada",
            "Cadastre um pagamento ou recebimento frequente para reduzir lançamentos manuais.",
            "↻",
        )
    else:
        recurring_df = pd.DataFrame(recurring_items)
        recurring_df["Situação"] = recurring_df["active"].map({True: "Ativa", False: "Pausada"})
        with st.container(key="rz_panel_recurring_list"):
            professional_table(
                recurring_df[["id", "description", "tx_type", "value", "frequency", "next_date", "Situação"]],
                max_visible_rows=8,
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
            selected_recurring = st.selectbox("Gerenciar recorrência", list(labels), format_func=lambda item_id: labels[item_id])
            selected_item = next(item for item in recurring_items if int(item["id"]) == int(selected_recurring))
            manage1, manage2 = st.columns(2)
            toggle_label = "Pausar recorrência" if selected_item["active"] else "Reativar recorrência"
            if manage1.button(toggle_label, width="stretch"):
                set_recurring_transaction_active(uid, int(selected_recurring), not selected_item["active"])
                st.rerun()
            if manage2.button("Excluir recorrência", width="stretch"):
                delete_recurring_transaction(uid, int(selected_recurring))
                st.rerun()

elif page == "Importar Extrato":
    from bank_import import (
        prepare_statement, is_probable_duplicate, suggest_category, suggest_statement_columns,
    )

    header("Importar Extrato", "Transforme CSV ou Excel do banco em lançamentos prontos para revisar.")
    st.markdown(
        """
        <div class="rz-step-grid">
          <div class="rz-step"><b>1 · Envie</b><span>Escolha o arquivo exportado pelo banco.</span></div>
          <div class="rz-step"><b>2 · Confira</b><span>Revise colunas, categorias e possíveis duplicidades.</span></div>
          <div class="rz-step"><b>3 · Confirme</b><span>Somente então os lançamentos são gravados.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="rz_panel_statement_upload"):
        st.caption("ARQUIVO BANCÁRIO")
        upload = st.file_uploader(
            "CSV, TXT ou Excel",
            type=["csv","txt","xlsx","xls"],
            key="statement_file",
            help="O arquivo é analisado somente após você enviá-lo.",
        )

    if upload:
        try:
            with st.spinner("Lendo o extrato..."):
                raw = cached_statement_frame(upload.getvalue(), upload.name)
            if raw.empty:
                st.warning("O arquivo não possui linhas para importar.")
            else:
                with st.container(key="rz_panel_statement_mapping"):
                    st.caption("CONFIRA AS COLUNAS")
                    professional_table(raw.head(8), max_visible_rows=8)
                    cols = list(raw.columns)
                    suggested_columns = suggest_statement_columns(raw)

                    def suggested_index(field: str, fallback: int) -> int:
                        suggested = suggested_columns.get(field)
                        return cols.index(suggested) if suggested in cols else min(fallback, len(cols) - 1)

                    a, b, cmap = st.columns(3)
                    date_col = a.selectbox("Data", cols, index=suggested_index("date", 0))
                    desc_col = b.selectbox("Descrição", cols, index=suggested_index("description", 1))
                    value_col = cmap.selectbox("Valor", cols, index=suggested_index("value", 2))
                    direction = st.segmented_control(
                        "Como interpretar os valores",
                        ["Sinal do valor", "Tudo como receita", "Tudo como despesa"],
                        default="Sinal do valor",
                        selection_mode="single",
                        key="statement_direction",
                        width="stretch",
                    ) or "Sinal do valor"
                    if all(suggested_columns.values()):
                        st.caption("✓ O Razync identificou as colunas automaticamente. Confirme antes de continuar.")

                prepared = prepare_statement(raw, date_col, desc_col, value_col, direction)
                learned_suggestions = [
                    learned_category(
                        row["Descrição"], row["Tipo"], transactions,
                        suggest_category(row["Descrição"], row["Tipo"]),
                    )
                    for _, row in prepared.iterrows()
                ]
                prepared["Categoria sugerida"] = [item["category"] for item in learned_suggestions]
                prepared["Confiança da categoria"] = [item["confidence"] for item in learned_suggestions]

                if prepared.empty:
                    st.warning("Nenhuma linha válida foi encontrada com esse mapeamento.")
                else:
                    prepared["Duplicado"] = [
                        is_probable_duplicate(
                            transactions, row["Data"], row["Tipo"],
                            row["Descrição"], row["Valor"],
                        )
                        for _, row in prepared.iterrows()
                    ]
                    with st.container(key="rz_panel_statement_review"):
                        st.caption("REVISÃO FINAL")
                        new_count = int((~prepared["Duplicado"]).sum())
                        duplicate_count = int(prepared["Duplicado"].sum())
                        r1, r2, r3 = st.columns(3)
                        r1.metric("Linhas válidas", len(prepared))
                        r2.metric("Novos lançamentos", new_count)
                        r3.metric("Possíveis duplicados", duplicate_count)
                        professional_table(
                            prepared,
                            max_visible_rows=10,
                            column_config={
                                "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                            },
                        )
                        only_new = st.checkbox("Ignorar possíveis duplicados", value=True)
                        rows_to_import = prepared[~prepared["Duplicado"]] if only_new else prepared
                        st.caption(f"{len(rows_to_import)} lançamento(s) serão importados.")
                        if st.button("Confirmar importação", type="primary", width="stretch"):
                            import_rows = [{
                                "tx_date": r["Data"],
                                "tx_type": r["Tipo"],
                                "description": r["Descrição"],
                                "category": r["Categoria sugerida"],
                                "value": float(r["Valor"]),
                                "document_number": "",
                                "counterparty": "",
                                "payment_method": "Banco",
                            } for _, r in rows_to_import.iterrows()]
                            try:
                                count = add_transactions_bulk(uid, import_rows)
                            except Exception:
                                st.error("A importação foi cancelada e nenhum lançamento foi salvo. Revise o arquivo e tente novamente.")
                            else:
                                st.success(f"{count} lançamento(s) importados.")
                                st.session_state["_navigate_to"] = "Movimentações"
                                st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível ler o arquivo: {exc}")

elif page == "Conciliação":
    header("Conciliação", "Encontre correspondências entre notas e recebimentos sem criar lançamentos duplicados.")
    rec, matches, duplicates = cached_reconciliation(transactions, invoices)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Notas emitidas", rec["total_invoices"])
    c2.metric("Conciliadas", rec["reconciled_invoices"])
    c3.metric("Sugestões", len(matches))
    c4.metric("Duplicidades", len(duplicates))

    section("Correspondências sugeridas", "O Razync sugere; você decide antes de qualquer vínculo.")
    if matches.empty:
        empty_state(
            "Nenhuma correspondência forte encontrada",
            "Importe um extrato ou registre receitas para comparar com suas notas.",
            "≈",
        )
    else:
        with st.container(key="rz_panel_reconciliation_matches"):
            show_matches = matches.rename(columns={
                "invoice_number":"Nota","customer":"Cliente","invoice_value":"Valor da nota",
                "tx_date":"Data do lançamento","tx_description":"Lançamento",
                "tx_value":"Valor lançado","score":"Pontuação",
                "confidence":"Confiança","reasons":"Motivos",
            })
            professional_table(
                show_matches[["Nota","Cliente","Valor da nota","Data do lançamento","Lançamento","Valor lançado","Confiança","Pontuação"]],
                max_visible_rows=8,
                column_config={
                    "Valor da nota": st.column_config.NumberColumn("Valor da nota", format="R$ %.2f"),
                    "Valor lançado": st.column_config.NumberColumn("Valor lançado", format="R$ %.2f"),
                    "Data do lançamento": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "Pontuação": st.column_config.ProgressColumn("Pontuação", min_value=0, max_value=100),
                },
            )
            matches = matches.reset_index(drop=True)
            option_labels = {
                index: (
                    f"Nota {row.invoice_number or row.invoice_id} → "
                    f"{row.tx_description} · confiança {row.confidence}"
                )
                for index, row in enumerate(matches.itertuples())
            }
            selected_match = st.selectbox(
                "Sugestão para revisar",
                list(option_labels.keys()),
                format_func=lambda x: option_labels[x],
                key="smart_match",
            )
            selected = matches.iloc[int(selected_match)]
            st.caption(f"{selected['reasons']} · pontuação {int(selected['score'])}/100")
            if st.button("Confirmar vínculo", type="primary", width="stretch"):
                link_transaction_document(
                    uid,
                    int(selected["tx_id"]),
                    str(selected["invoice_number"] or ""),
                    str(selected["customer"] or ""),
                )
                st.success("Nota vinculada ao lançamento existente.")
                st.rerun()

    pending_inv = rec["pending_invoices"]
    with st.expander(f"Notas ainda sem vínculo · {len(pending_inv)}", expanded=bool(len(pending_inv)) and matches.empty):
        if pending_inv.empty:
            st.success("Todas as notas numeradas estão conciliadas.")
        else:
            professional_table(
                pending_inv,
                max_visible_rows=8,
                column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
            )
            selected_invoice = st.selectbox("Nota", pending_inv["ID"].tolist(), key="rec_invoice")
            source = invoices[invoices["id"] == selected_invoice].iloc[0]
            st.caption("Crie uma receita somente quando não existir um recebimento correspondente.")
            if st.button("Criar receita desta nota", width="stretch"):
                issue = source["issue_date"]
                tx_date_value = issue.date() if hasattr(issue, "date") else issue
                invoice_type_value = str(source.get("invoice_type") or "")
                revenue_category = (
                    "Serviços" if invoice_type_value == "Serviço"
                    else "Indústria" if "Indústr" in invoice_type_value or "Industr" in invoice_type_value
                    else "Comércio"
                )
                add_transaction(
                    uid, tx_date=tx_date_value, tx_type="Receita",
                    description=source.get("description") or f"Nota {source.get('number') or ''}",
                    category=revenue_category,
                    value=float(source.get("amount") or 0),
                    document_number=str(source.get("number") or ""),
                    counterparty=str(source.get("customer") or ""),
                    payment_method="Outro",
                )
                st.rerun()

    with st.expander(f"Possíveis duplicidades · {len(duplicates)}"):
        if duplicates.empty:
            st.success("Nenhuma duplicidade evidente foi encontrada.")
        else:
            professional_table(
                duplicates,
                max_visible_rows=8,
                column_config={
                    "tx_date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "value": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                },
            )
            duplicate_id = st.selectbox("Lançamento a excluir", duplicates["id"].tolist(), key="duplicate_delete")
            st.caption("Confira os registros antes de excluir.")
            if st.button("Excluir lançamento selecionado", key="remove_duplicate", width="stretch"):
                deleted = transactions.loc[transactions["id"] == duplicate_id].iloc[0].to_dict()
                st.session_state["_undo_transaction"] = transaction_restore_payload(deleted)
                delete_transaction(uid, int(duplicate_id))
                st.rerun()

    if st.button("Importar novo extrato", key="reconciliation_import", width="stretch"):
        st.session_state["_navigate_to"] = "Importar Extrato"
        st.rerun()

elif page == "Fluxo de Caixa":
    import plotly.express as px

    header("Fluxo de Caixa", "Acompanhe entradas, saídas e saldo acumulado mês a mês.")
    year = st.selectbox("Ano", list(range(CURRENT_YEAR-3, CURRENT_YEAR+1)), index=3, key="cashflow_year")
    cf = cashflow_monthly(transactions, year)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entradas", brl(float(cf["Entradas"].sum())))
    c2.metric("Saídas", brl(float(cf["Saídas"].sum())))
    c3.metric("Resultado", brl(float(cf["Resultado"].sum())))
    c4.metric("Resultado acumulado", brl(float(cf["Resultado acumulado"].iloc[-1]) if not cf.empty else 0.0))

    with st.container(key="rz_panel_cashflow_chart"):
        st.caption("EVOLUÇÃO")
        fig = px.bar(cf, x="Mês", y=["Entradas","Saídas"], barmode="group", template=PLOT_TEMPLATE)
        apply_plot_theme(fig, UI_THEME, height=310)
        fig.update_layout(margin=dict(l=8, r=8, t=18, b=8), legend_title_text=None)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with st.expander("Ver valores por mês", expanded=False):
        professional_table(
            cf,
            max_visible_rows=12,
            column_config={
                "Entradas": st.column_config.NumberColumn(format="R$ %.2f"),
                "Saídas": st.column_config.NumberColumn(format="R$ %.2f"),
                "Resultado": st.column_config.NumberColumn(format="R$ %.2f"),
                "Resultado acumulado": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )

elif page == "Análise Financeira":
    import plotly.express as px

    header("Análise Financeira", "Entenda evolução, margem, despesas e pontos que merecem atenção.")
    analysis_year = st.selectbox("Ano da análise", list(range(CURRENT_YEAR-3, CURRENT_YEAR+1)), index=3, key="analysis_year")
    analysis = financial_analysis(transactions, analysis_year)

    ac1, ac2, ac3, ac4 = st.columns(4)
    ac1.metric("Receitas", brl(analysis["revenue"]))
    ac2.metric("Despesas", brl(analysis["expense"]))
    ac3.metric("Resultado", brl(analysis["result"]))
    ac4.metric("Margem", f"{analysis['margin']:.1f}%")

    analysis_limit = annual_limit_for(opening, analysis_year, profile.get("annual_limit"))
    section("Leitura automática", "O que os números cadastrados indicam em linguagem simples.")
    for insight in financial_story(
        analysis["revenue"],
        analysis["expense"],
        analysis["revenue"],
        analysis_limit,
        period_label="ano",
    ):
        alert_card(insight["tone"], insight["title"], insight["detail"])

    monthly = analysis["monthly"]
    if not monthly.empty:
        with st.container(key="rz_panel_analysis_evolution"):
            st.caption("EVOLUÇÃO MENSAL")
            fig = px.line(monthly, x="Mês", y=["Receitas","Despesas","Resultado"], markers=True, template=PLOT_TEMPLATE)
            apply_plot_theme(fig, UI_THEME, height=310)
            fig.update_layout(margin=dict(l=8, r=8, t=18, b=8), legend_title_text=None)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        section("Despesas por categoria")
        bycat = analysis["expense_categories"]
        if bycat.empty:
            st.info("Sem despesas registradas neste ano.")
        else:
            fig2 = px.bar(bycat, x="Categoria", y="Valor", template=PLOT_TEMPLATE)
            apply_plot_theme(fig2, UI_THEME, height=285)
            fig2.update_layout(margin=dict(l=8, r=8, t=18, b=8))
            st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
    with right:
        section("Revisões recomendadas")
        analysis_transactions = (
            transactions[transactions["tx_date"].dt.year == analysis_year]
            if not transactions.empty else transactions
        )
        analysis_invoices = (
            invoices[invoices["issue_date"].dt.year == analysis_year]
            if not invoices.empty else invoices
        )
        analysis_das = [
            item for item in das_rows
            if str(item.get("competence") or "").startswith(str(analysis_year))
        ]
        checks = consistency_checks(analysis_transactions, analysis_invoices, analysis_das)
        actionable_checks = [
            item for item in checks
            if str(item.get("Nível") or "") != "OK"
        ]
        if not actionable_checks:
            st.success("Nenhuma inconsistência básica identificada neste ano.")
        else:
            for item in actionable_checks:
                tone = "danger" if item.get("Nível") == "Crítico" else "warn"
                quantity = int(item.get("Quantidade") or 0)
                alert_card(
                    tone,
                    str(item.get("Verificação") or "Revisar informação"),
                    f"{quantity} ocorrência(s) encontrada(s) no ano selecionado.",
                )

    with st.expander("Ver tabela mensal"):
        if not monthly.empty:
            professional_table(
                monthly,
                max_visible_rows=12,
                column_config={col: st.column_config.NumberColumn(format="R$ %.2f") for col in ["Receitas","Despesas","Resultado"]},
            )

    analysis_pdf = cached_financial_summary_pdf(profile, analysis_year, analysis)
    st.download_button(
        "Baixar análise financeira em PDF",
        analysis_pdf,
        file_name=f"analise_financeira_{analysis_year}.pdf",
        mime="application/pdf",
        width="stretch",
    )

elif page == "Fechamento Mensal":
    header("Fechamento Mensal", "Confira o mês em uma sequência simples antes de considerá-lo organizado.")
    a, b = st.columns(2)
    close_year = a.selectbox("Ano", list(range(CURRENT_YEAR-2, CURRENT_YEAR+1)), index=2, key="close_year")
    close_month = b.selectbox("Mês", list(range(1,13)), index=date.today().month-1, format_func=lambda m: MONTH_NAMES_PT[m - 1], key="close_month")
    closing = monthly_closing(transactions, invoices, docs, das_rows, close_year, close_month)
    closing_tx = closing.get("transactions")
    no_movement_registered = bool(closing_tx is not None and closing_tx.empty)

    if no_movement_registered:
        st.info("Não há movimentações registradas nesta competência. Se o mês realmente não teve movimento, o Razync ainda trata isso como uma informação a confirmar, não como erro fiscal.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Receitas", brl(closing["revenue"]))
    m2.metric("Despesas", brl(closing["expense"]))
    m3.metric("Resultado", brl(closing["result"]))
    m4.metric("Organização", f"{closing['score']}%")
    st.progress(closing["score"] / 100)

    section("Checklist do mês", "Resolva somente o que ainda estiver pendente.")
    closing_routes = {
        "Movimentações do mês revisadas": "Movimentações",
        "Receitas registradas": "Movimentações",
        "DAS da competência criado": "DAS",
        "Documentos da competência armazenados": "Documentos",
        "Lançamentos com documento informado": "Movimentações",
        "Notas fiscais conferidas": "Notas Fiscais",
    }
    with st.container(key="rz_panel_closing_steps"):
        for index, item in enumerate(closing["checklist"], start=1):
            status_col, detail_col, action_col = st.columns([.65, 4.5, 1.2])
            status_col.markdown("### ✓" if item["OK"] else f"### {index}")
            detail_col.write(f"**{item['Item']}**")
            detail_col.caption(item["Detalhe"])
            if not item["OK"]:
                route = closing_routes[item["Item"]]
                if action_col.button("Resolver", key=f"closing_step_{index}", width="stretch"):
                    st.session_state["_navigate_to"] = route
                    st.rerun()

    if closing["score"] == 100:
        st.success("Organização do mês concluída com base nos dados cadastrados.")
    else:
        pending_count = sum(1 for item in closing["checklist"] if not item["OK"])
        st.info(f"Há {pending_count} ponto(s) a revisar antes de considerar este mês organizado.")

    closing_pdf = cached_closing_summary_pdf(profile, close_year, close_month, closing)
    st.download_button(
        "Baixar fechamento em PDF",
        closing_pdf,
        file_name=f"fechamento_{close_year}_{close_month:02d}.pdf",
        mime="application/pdf",
        width="stretch",
    )

elif page == "Relatório Mensal":
    header("Relatório Mensal", "Veja a composição das receitas e gere o PDF da competência desejada.")
    year = st.selectbox("Ano", list(range(CURRENT_YEAR-3, CURRENT_YEAR+1)), index=3, key="rmyear")
    rows = monthly_rows(transactions, year)
    dfm = pd.DataFrame([
        {
            "Mês": r["month_name"],
            "Com documento": r["with_doc"],
            "Sem documento": r["without_doc"],
            "Comércio": r["commerce"],
            "Indústria": r["industry"],
            "Serviços": r["services"],
            "Total": r["total"],
        }
        for r in rows
    ])
    total_year = float(dfm["Total"].sum()) if not dfm.empty else 0.0
    if year == CURRENT_YEAR:
        first_month = opening.month if opening and opening.year == year else 1
        elapsed_months = max(date.today().month - first_month + 1, 1)
    elif opening and opening.year == year:
        elapsed_months = max(13 - opening.month, 1)
    else:
        elapsed_months = 12
    r1, r2 = st.columns(2)
    r1.metric("Receita no ano", brl(total_year))
    r2.metric("Média mensal", brl(total_year / elapsed_months if total_year else 0.0))

    with st.container(key="rz_panel_monthly_report"):
        st.caption("VISÃO ANUAL")
        professional_table(
            dfm,
            max_visible_rows=12,
            column_config={
                col: st.column_config.NumberColumn(format="R$ %.2f")
                for col in ["Com documento","Sem documento","Comércio","Indústria","Serviços","Total"]
            },
        )

    with st.container(key="rz_panel_monthly_pdf"):
        st.caption("GERAR PDF")
        default_month = date.today().month if year == CURRENT_YEAR else 12
        month = st.selectbox(
            "Competência",
            list(range(1,13)),
            index=default_month - 1,
            format_func=lambda m: MONTH_NAMES_PT[m - 1],
            key="pdfmonth",
        )
        selected_row = rows[month-1]
        pdf = cached_monthly_report_pdf(profile, year, [selected_row])
        st.download_button(
            "Baixar relatório em PDF",
            pdf,
            file_name=f"relatorio_mensal_{year}_{month:02d}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.caption("O PDF do Razync é um resumo de apoio. Para cumprir a obrigação formal, confira/preencha o Relatório Mensal oficial e mantenha-o arquivado com os documentos.")
        st.link_button(
            "Abrir Relatório Mensal oficial",
            OFFICIAL_SERVICES["monthly_report"]["url"],
            width="stretch",
        )

elif page == "Notas Fiscais":
    header("Notas Fiscais", "Emissão, cadastro e histórico em um fluxo único.")

    total_notes = len(invoices)
    active_invoices = (
        invoices[invoices["status"] == "Emitida"]
        if not invoices.empty and "status" in invoices.columns
        else invoices
    )
    total_amount = (
        float(active_invoices["amount"].sum())
        if not active_invoices.empty and "amount" in active_invoices.columns
        else 0.0
    )
    month_notes = (
        active_invoices[
            (active_invoices["issue_date"].dt.year == CURRENT_YEAR)
            & (active_invoices["issue_date"].dt.month == date.today().month)
        ]
        if not active_invoices.empty else active_invoices
    )
    month_amount = float(month_notes["amount"].sum()) if not month_notes.empty else 0.0

    n1, n2, n3 = st.columns(3)
    with n1:
        stat_card("Notas", str(total_notes), detail="cadastradas")
    with n2:
        stat_card("Emitido no mês", brl(month_amount), detail="notas ativas")
    with n3:
        stat_card("Emitido acumulado", brl(total_amount), detail="notas ativas")

    activity_type = str(profile.get("activity_type") or "")
    service_activity = activity_type in {"Serviços", "Misto"} or not activity_type

    official_col, official_action = st.columns([2, .9], gap="large")
    with official_col:
        st.caption("EMISSÃO OFICIAL")
        if service_activity:
            st.markdown("**Serviços do MEI usam o padrão nacional de NFS-e.**")
            st.caption(
                "A emissão acontece no ambiente oficial. O Razync organiza os dados e nunca pede sua senha gov.br."
            )
        else:
            st.markdown("**Comércio e indústria podem depender da SEFAZ do estado.**")
            st.caption(
                "O Razync registra e organiza a nota sem presumir qual emissor estadual é o correto."
            )
    with official_action:
        if service_activity:
            st.link_button(
                "Abrir Emissor Nacional",
                OFFICIAL_SERVICES["nfse"]["url"],
                type="primary",
                width="stretch",
            )
            if st.button(
                "Importar NFS-e",
                key="open_nfse_import",
                width="stretch",
            ):
                st.session_state["_navigate_to"] = "Importar NFS-e"
                st.rerun()

    st.markdown("#### Cadastrar nota")
    with st.form("invoice_form", clear_on_submit=True):
        a, b, ccol = st.columns([1, 1, 1])
        issue = a.date_input("Emissão", value=date.today())
        inv_type = b.selectbox("Tipo", ["Serviço", "Comércio", "Indústria"])
        amount = ccol.number_input(
            "Valor",
            min_value=0.0,
            step=10.0,
            format="%.2f",
        )

        a, b = st.columns(2)
        number = a.text_input("Número da nota")
        customer = b.text_input("Cliente", placeholder="Nome do cliente")
        desc = st.text_input(
            "Descrição",
            placeholder="Serviço prestado ou venda realizada",
        )

        with st.expander("Detalhes opcionais"):
            a, b = st.columns(2)
            custdoc = a.text_input("CPF/CNPJ do cliente")
            status = b.selectbox("Situação", ["Emitida", "Cancelada"])

        submit = st.form_submit_button(
            "Salvar nota",
            type="primary",
        )
        if submit:
            clean_number = number.strip()
            existing_numbers = (
                set(invoices["number"].fillna("").astype(str).str.strip())
                if not invoices.empty and "number" in invoices.columns
                else set()
            )
            existing_numbers.discard("")
            if amount <= 0:
                st.error("Informe um valor maior que zero.")
            elif clean_number and clean_number in existing_numbers:
                st.error("Já existe uma nota com esse número.")
            else:
                add_invoice(
                    uid,
                    issue_date=issue,
                    invoice_type=inv_type,
                    number=clean_number,
                    customer=customer.strip(),
                    customer_document=custdoc.strip(),
                    description=desc.strip(),
                    amount=amount,
                    status=status,
                )
                st.rerun()

    st.markdown("#### Histórico")
    if invoices.empty:
        empty_state(
            "Nenhuma nota cadastrada",
            "Cadastre ou importe suas notas para acompanhar o faturamento.",
            "▤",
        )
    else:
        view_columns = [
            column for column in [
                "id", "issue_date", "invoice_type", "number",
                "customer", "amount", "status",
            ]
            if column in invoices.columns
        ]
        professional_table(
            invoices[view_columns],
            max_visible_rows=10,
            column_config={
                "id": None,
                "amount": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "issue_date": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
            },
        )

        with st.expander("Gerenciar notas"):
            edit_tab, delete_tab = st.tabs(["Editar", "Excluir"])

            with edit_tab:
                edit_iid = st.selectbox(
                    "Nota",
                    invoices["id"].tolist(),
                    format_func=lambda value: (
                        f"{invoices.loc[invoices['id'] == value, 'number'].iloc[0] or '#'+str(value)} · "
                        f"{invoices.loc[invoices['id'] == value, 'customer'].iloc[0] or 'Sem cliente'}"
                    ),
                    key="editinv",
                )
                invoice_row = invoices.loc[invoices["id"] == edit_iid].iloc[0]
                raw_issue = invoice_row["issue_date"]
                issue_value = raw_issue.date() if hasattr(raw_issue, "date") else raw_issue
                current_type = str(invoice_row.get("invoice_type") or "Serviço")
                type_options = ["Serviço", "Comércio", "Indústria"]
                if current_type not in type_options:
                    type_options = [current_type, *type_options]

                with st.form("edit_invoice_form"):
                    a, b, d = st.columns(3)
                    edit_issue = a.date_input("Emissão", value=issue_value)
                    edit_type = b.selectbox(
                        "Tipo",
                        type_options,
                        index=type_options.index(current_type),
                    )
                    edit_amount = d.number_input(
                        "Valor",
                        min_value=0.01,
                        value=float(invoice_row.get("amount") or 0.01),
                        step=10.0,
                        format="%.2f",
                    )
                    a, b = st.columns(2)
                    edit_number = a.text_input(
                        "Número",
                        value=str(invoice_row.get("number") or ""),
                    )
                    edit_customer = b.text_input(
                        "Cliente",
                        value=str(invoice_row.get("customer") or ""),
                    )
                    edit_description = st.text_input(
                        "Descrição",
                        value=str(invoice_row.get("description") or ""),
                    )
                    with st.expander("Detalhes"):
                        a, b = st.columns(2)
                        edit_customer_document = a.text_input(
                            "CPF/CNPJ",
                            value=str(invoice_row.get("customer_document") or ""),
                        )
                        current_status = str(invoice_row.get("status") or "Emitida")
                        edit_status = b.selectbox(
                            "Situação",
                            ["Emitida", "Cancelada"],
                            index=1 if current_status == "Cancelada" else 0,
                        )
                    save_invoice_edit = st.form_submit_button(
                        "Salvar alterações",
                        type="primary",
                    )

                if save_invoice_edit:
                    clean_number = edit_number.strip()
                    other_numbers = set(
                        invoices.loc[invoices["id"] != edit_iid, "number"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )
                    other_numbers.discard("")
                    if clean_number and clean_number in other_numbers:
                        st.error("Outra nota já usa esse número.")
                    else:
                        update_invoice(
                            uid,
                            int(edit_iid),
                            issue_date=edit_issue,
                            invoice_type=edit_type,
                            number=clean_number,
                            customer=edit_customer.strip(),
                            customer_document=edit_customer_document.strip(),
                            description=edit_description.strip(),
                            amount=edit_amount,
                            status=edit_status,
                        )
                        st.rerun()

            with delete_tab:
                iid = st.selectbox(
                    "Nota",
                    invoices["id"].tolist(),
                    format_func=lambda value: (
                        f"{invoices.loc[invoices['id'] == value, 'number'].iloc[0] or '#'+str(value)} · "
                        f"{invoices.loc[invoices['id'] == value, 'customer'].iloc[0] or 'Sem cliente'}"
                    ),
                    key="delinv",
                )
                st.caption("A exclusão é definitiva.")
                if st.button(
                    "Excluir nota",
                    key="delete_invoice_btn",
                ):
                    delete_invoice(uid, int(iid))
                    st.rerun()

elif page == "Importar NFS-e":
    header("Importar NFS-e", "Traga as notas exportadas do portal oficial sem digitar uma por uma.")
    st.markdown(
        """
        <div class="rz-step-grid">
          <div class="rz-step"><b>1 · Exporte</b><span>Baixe CSV ou Excel no emissor.</span></div>
          <div class="rz-step"><b>2 · Mapeie</b><span>Confirme quais colunas representam cada campo.</span></div>
          <div class="rz-step"><b>3 · Importe</b><span>Somente notas novas são adicionadas.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="rz_panel_nfse_import"):
        st.caption("ARQUIVO DE NFS-E")
        nfse_file = st.file_uploader(
            "CSV ou Excel",
            type=["csv", "xlsx", "xls"],
            key="nfse_import",
            help="O arquivo-fonte é usado apenas durante a importação.",
        )

    if nfse_file is not None:
        try:
            nfse_frame = read_nfse_export(nfse_file)
        except ValueError as exc:
            st.error(str(exc))
        else:
            with st.container(key="rz_panel_nfse_mapping"):
                st.caption("MAPEAMENTO")
                suggestions = suggest_nfse_columns(nfse_frame.columns)
                options = ["—"] + list(nfse_frame.columns)
                labels = {
                    "date": "Data de emissão",
                    "number": "Número da nota",
                    "amount": "Valor",
                    "customer": "Cliente/tomador",
                    "document": "CPF/CNPJ",
                    "description": "Descrição",
                    "status": "Situação",
                }
                mapping = {}
                fields = list(labels.items())
                for index in range(0, len(fields), 2):
                    cols = st.columns(2)
                    for offset, (field, label) in enumerate(fields[index:index+2]):
                        suggested = suggestions.get(field)
                        selected_index = options.index(suggested) if suggested in options else 0
                        selected = cols[offset].selectbox(
                            label,
                            options,
                            index=selected_index,
                            key=f"nfse_{field}",
                        )
                        mapping[field] = None if selected == "—" else selected

            try:
                nfse_rows = normalize_nfse(nfse_frame, mapping)
            except ValueError as exc:
                st.warning(str(exc))
                nfse_rows = []

            if nfse_rows:
                existing_numbers = (
                    set(invoices["number"].fillna("").astype(str))
                    if not invoices.empty else set()
                )
                new_rows = [row for row in nfse_rows if row["number"] not in existing_numbers]
                with st.container(key="rz_panel_nfse_review"):
                    st.caption("REVISÃO")
                    a, b, d = st.columns(3)
                    a.metric("Lidas", len(nfse_rows))
                    b.metric("Novas", len(new_rows))
                    d.metric("Já cadastradas", len(nfse_rows) - len(new_rows))
                    professional_table(pd.DataFrame(nfse_rows), max_visible_rows=8)
                    if st.button(
                        "Importar notas novas",
                        type="primary",
                        width="stretch",
                        disabled=not new_rows,
                    ):
                        for row in new_rows:
                            add_invoice(uid, **row)
                        st.success(f"{len(new_rows)} nota(s) importada(s).")
                        st.session_state["_navigate_to"] = "Notas Fiscais"
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
    header("DAS Mensal", "Gere a guia no portal oficial e acompanhe vencimento, pagamento e documento em um só lugar.")

    with st.container(key="rz_panel_das_period"):
        st.caption("COMPETÊNCIA")
        ycol, mcol = st.columns(2)
        year = ycol.selectbox("Ano", list(range(CURRENT_YEAR-2, CURRENT_YEAR+1)), index=2, key="dasyear")
        month = mcol.selectbox(
            "Mês",
            list(range(1,13)),
            index=date.today().month - 1,
            format_func=lambda m: MONTH_NAMES_PT[m - 1],
            key="dasmonth",
        )
    competence = f"{year}-{month:02d}"
    official_pgmei_url = OFFICIAL_SERVICES["das"]["url"]
    payment_suggestions = das_payment_matches(das_rows, transactions)
    journey = das_journey(competence, das_rows, docs, payment_suggestions)
    current_das = next((item for item in das_rows if item.get("competence") == competence), None)

    current_due = current_das.get("due_date") if current_das else None
    if isinstance(current_due, str):
        try:
            current_due = date.fromisoformat(current_due[:10])
        except ValueError:
            current_due = None
    due_default = current_due if isinstance(current_due, date) else das_due_date(competence)

    current_payment = current_das.get("payment_date") if current_das else None
    if isinstance(current_payment, str):
        try:
            current_payment = date.fromisoformat(current_payment[:10])
        except ValueError:
            current_payment = None
    payment_default = current_payment if isinstance(current_payment, date) else date.today()

    amount_default = float(current_das.get("amount") or 0) if current_das else 0.0
    status_default = str(current_das.get("status") or "Pendente") if current_das else "Pendente"
    notes_default = str(current_das.get("notes") or "") if current_das else ""

    s1, s2, s3 = st.columns(3)
    s1.metric("Organização", f"{journey['percent']}%")
    s2.metric(
        "Situação",
        das_status(current_das.get("status", "Pendente"), current_das.get("due_date"))
        if current_das else "Não registrado",
    )
    s3.metric(
        "Valor",
        brl(float(current_das.get("amount") or 0)) if current_das else "—",
    )

    section("Andamento", "Veja rapidamente o que já foi concluído nesta competência.")
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

    issue_col, register_col = st.columns([1.1, 1], gap="large")
    with issue_col, st.container(key="rz_panel_das_official"):
        st.caption("GERAR GUIA OFICIAL")
        st.markdown(
            """
            <div class="rz-step-grid">
              <div class="rz-step"><b>1 · Abra o PGMEI</b><span>Use o portal oficial da Receita Federal.</span></div>
              <div class="rz-step"><b>2 · Gere o DAS</b><span>Escolha a competência correta.</span></div>
              <div class="rz-step"><b>3 · Volte ao Razync</b><span>Registre valor, status e PDF.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cnpj = str(profile.get("cnpj") or "").strip()
        if cnpj:
            st.code(cnpj, language=None)
            st.caption("CNPJ cadastrado no Razync.")
        else:
            st.warning("Cadastre o CNPJ em Meu MEI antes de gerar a guia.")
        st.link_button(
            "Abrir PGMEI oficial",
            official_pgmei_url,
            type="primary",
            width="stretch",
            help="Abre o site oficial da Receita Federal.",
        )
        st.caption("O Razync não solicita nem armazena sua senha gov.br.")

    with register_col, st.container(key="rz_panel_das_register"):
        st.caption("REGISTRAR CONTROLE")
        due = st.date_input(
            "Vencimento (confirme na guia)",
            value=due_default,
            key=f"das_due_{competence}",
        )
        st.caption("A guia oficial prevalece, inclusive quando feriado altera o vencimento.")
        amount = st.number_input(
            "Valor do DAS",
            min_value=0.0,
            value=amount_default,
            step=1.0,
            format="%.2f",
            key=f"das_amount_{competence}",
        )
        status = st.selectbox(
            "Situação",
            ["Pendente","Pago"],
            index=1 if status_default == "Pago" else 0,
            key=f"das_status_{competence}",
        )
        payment_date = None
        if status == "Pago":
            payment_date = st.date_input(
                "Data de pagamento",
                value=payment_default,
                key=f"das_payment_date_{competence}",
            )
        guide = st.file_uploader(
            "Guia oficial em PDF",
            type=["pdf"],
            key=f"das_guide_upload_{competence}",
            help="Opcional. O arquivo será guardado junto aos documentos.",
        )
        if guide is not None:
            with st.spinner("Lendo a guia..."):
                guide_analysis = cached_das_guide_analysis(guide.getvalue(), guide.name)
            ga1, ga2 = st.columns(2)
            ga1.metric("Competência lida", guide_analysis["competence"] or "—")
            ga2.metric(
                "Valor provável",
                brl(guide_analysis["amount"]) if guide_analysis["amount"] is not None else "—",
            )
            if guide_analysis["competence"] and guide_analysis["competence"] != competence:
                st.warning("A competência identificada no PDF é diferente da selecionada.")
            for guide_warning in guide_analysis["warnings"]:
                st.info(guide_warning)
        notes = st.text_area(
            "Observações",
            value=notes_default,
            key=f"das_notes_{competence}",
            height=90,
        )
        if st.button("Salvar controle do DAS", type="primary", width="stretch"):
            if amount <= 0:
                st.warning("Informe o valor exibido na guia oficial.")
            else:
                try:
                    upsert_das(uid, competence, due, amount, status, payment_date, notes)
                    if guide is not None:
                        save_uploaded_document(user, guide, "DAS", competence)
                except Exception:
                    st.error("Não foi possível salvar o controle do DAS agora.")
                else:
                    st.success("DAS registrado.")
                    st.rerun()

    competence_matches = [
        item for item in payment_suggestions if item.get("competence") == competence
    ]
    if competence_matches and current_das:
        match = competence_matches[0]
        alert_card(
            "warn",
            "Possível pagamento encontrado no extrato",
            f"{match['date'].strftime('%d/%m/%Y')} · {brl(match['value'])} · confiança {match['score']}%.",
        )
        if st.button("Conferi e quero marcar como pago", key="confirm_das_match", width="stretch"):
            upsert_das(
                uid, competence, current_das.get("due_date"),
                float(current_das.get("amount") or match["value"]),
                "Pago", match["date"],
                (str(current_das.get("notes") or "") + "\nPagamento conciliado com movimentação após confirmação do usuário.").strip(),
            )
            st.success("Pagamento confirmado.")
            st.rerun()

    section("Competências do ano", "Acompanhe o histórico sem abrir uma competência por vez.")
    current = [d for d in das_rows if str(d["competence"]).startswith(str(year))]
    if not current:
        empty_state(
            "Nenhum DAS controlado neste ano",
            "Gere a guia no PGMEI e registre a competência para acompanhar vencimento e pagamento.",
            "▣",
        )
    else:
        das_view = [
            {
                "Competência": d["competence"],
                "Vencimento": d["due_date"],
                "Valor": d["amount"],
                "Status": das_status(d["status"], d["due_date"]),
                "Pagamento": d["payment_date"],
            }
            for d in current
        ]
        professional_table(
            pd.DataFrame(das_view),
            max_visible_rows=12,
            column_config={
                "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
                "Vencimento": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Pagamento": st.column_config.DateColumn(format="DD/MM/YYYY"),
            },
        )
        st.caption("A data e o valor impressos na guia oficial sempre prevalecem.")

elif page == "DASN-SIMEI":
    header("DASN-SIMEI", "Prepare e confira os números anuais antes de acessar a declaração oficial.")
    year = st.selectbox("Ano-calendário", list(range(CURRENT_YEAR-4, CURRENT_YEAR+1)), index=3, key="dasnyear")
    services, sales = category_totals_for_dasn(transactions, year)
    total = services + sales

    if year == CURRENT_YEAR:
        st.info("O ano-calendário ainda está em andamento. Este resumo é parcial e serve para acompanhamento; a declaração anual deve usar os valores finais do ano encerrado.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Serviços", brl(services))
    c2.metric("Comércio/indústria", brl(sales))
    c3.metric("Receita bruta total", brl(total))

    with st.container(key="rz_panel_dasn_summary"):
        st.caption("RESUMO PARA CONFERÊNCIA")
        employee = st.checkbox(
            "O MEI teve empregado no ano?",
            value=bool(employees) or bool(profile.get("has_employee", False)),
        )
        pdf = cached_dasn_summary_pdf(profile, year, services, sales, employee)
        st.download_button(
            "Baixar resumo para conferência",
            pdf,
            file_name=f"resumo_DASN_{year}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.caption("O Razync organiza as informações, mas não transmite a DASN-SIMEI.")
        st.link_button(
            "Abrir serviço oficial da DASN-SIMEI",
            OFFICIAL_SERVICES["dasn"]["url"],
            type="primary",
            width="stretch",
        )

elif page == "Obrigações":
    header("Prazos e Obrigações", "Acompanhe compromissos automáticos do MEI e tarefas específicas do negócio.")
    obligation_year = st.selectbox("Ano", list(range(CURRENT_YEAR-1, CURRENT_YEAR+2)), index=1, key="obyear")
    auto = automatic_obligations(obligation_year, opening)
    manual = obligations
    today_value = date.today()
    soon_limit = today_value.fromordinal(today_value.toordinal() + 15)

    das_by_competence = {
        str(item.get("competence") or ""): item
        for item in das_rows
    }

    combined = []
    attention_count = 0
    for row in auto:
        status_value = row["status"]
        if str(row.get("title") or "").startswith("DAS "):
            actual_das = das_by_competence.get(str(row.get("competence") or ""))
            if actual_das:
                status_value = das_status(
                    actual_das.get("status", "Pendente"),
                    actual_das.get("due_date"),
                    today_value,
                )
            due_value = row.get("due_date")
            if status_value == "Atrasado":
                attention_count += 1
            elif status_value == "Pendente" and due_value and today_value <= due_value <= soon_limit:
                attention_count += 1
        elif status_value == "Próxima":
            attention_count += 1

        combined.append({
            "Origem": "Automática",
            "Obrigação": row["title"],
            "Tipo": row["category"],
            "Competência": row["competence"],
            "Vencimento": row["due_date"],
            "Status": status_value,
            "Detalhes": row["details"],
        })

    for row in manual:
        due_value = row.get("due_date")
        if isinstance(due_value, str):
            try:
                due_value = date.fromisoformat(due_value[:10])
            except ValueError:
                due_value = None
        manual_status = str(row.get("status") or "Pendente")
        if manual_status != "Concluído" and due_value and due_value <= soon_limit:
            attention_count += 1
        combined.append({
            "Origem": "Manual",
            "Obrigação": row["title"],
            "Tipo": row["category"],
            "Competência": "-",
            "Vencimento": due_value,
            "Status": manual_status,
            "Detalhes": row["notes"],
        })

    manual_count = len(manual)
    o1, o2, o3 = st.columns(3)
    o1.metric("Itens no calendário", len(combined))
    o2.metric("Atenção agora", attention_count)
    o3.metric("Personalizadas", manual_count)

    st.caption("Prazos automáticos ajudam na organização. “Prazo passado” não confirma descumprimento; confira o que já foi realizado e os documentos oficiais.")
    if combined:
        with st.container(key="rz_panel_obligations_list"):
            obd = pd.DataFrame(combined).sort_values("Vencimento")
            professional_table(
                obd,
                max_visible_rows=10,
                column_config={"Vencimento": st.column_config.DateColumn(format="DD/MM/YYYY")},
            )
    else:
        empty_state(
            "Nenhuma obrigação para exibir",
            "Quando houver tarefas automáticas ou personalizadas, elas aparecerão aqui.",
            "✓",
        )

    with st.expander("Adicionar obrigação personalizada"):
        with st.form("obl_form", clear_on_submit=True):
            title = st.text_input("Título")
            due = st.date_input("Vencimento", value=date.today())
            cat = st.selectbox("Categoria", ["Fiscal","Financeira","Administrativa","Trabalhista","Outra"])
            notes = st.text_area("Observações")
            if st.form_submit_button("Adicionar obrigação", type="primary", width="stretch"):
                if title.strip():
                    add_obligation(
                        uid, title=title.strip(), due_date=due, status="Pendente",
                        category=cat, notes=notes.strip(),
                    )
                    st.rerun()
                else:
                    st.error("Informe um título para a obrigação.")

    if manual:
        with st.expander("Gerenciar obrigações personalizadas"):
            item = st.selectbox(
                "Tarefa",
                [o["id"] for o in manual],
                format_func=lambda x: next(o["title"] for o in manual if o["id"] == x),
            )
            selected_manual = next(o for o in manual if int(o["id"]) == int(item))
            current_manual_status = str(selected_manual.get("status") or "Pendente")
            status = st.selectbox(
                "Novo status",
                ["Pendente","Concluído"],
                index=1 if current_manual_status == "Concluído" else 0,
                key="oblstatus",
            )
            c1, c2 = st.columns(2)
            if c1.button("Atualizar", width="stretch"):
                update_obligation_status(uid, int(item), status)
                st.rerun()
            if c2.button("Excluir", width="stretch"):
                delete_obligation(uid, int(item))
                st.rerun()

elif page == "Clientes e Fornecedores":
    header("Clientes e Fornecedores", "Organize os contatos que aparecem nas vendas, compras e documentos.")

    client_count = sum(1 for item in contacts if item.get("contact_type") == "Cliente")
    supplier_count = sum(1 for item in contacts if item.get("contact_type") == "Fornecedor")
    c1, c2, c3 = st.columns(3)
    c1.metric("Contatos", len(contacts))
    c2.metric("Clientes", client_count)
    c3.metric("Fornecedores", supplier_count)

    form_col, tip_col = st.columns([1.55, .85], gap="large")
    with form_col, st.container(key="rz_panel_contacts_new"):
        st.caption("NOVO CONTATO")
        with st.form("contact_form", clear_on_submit=True):
            a, b = st.columns([1, 2])
            typ = a.segmented_control(
                "Tipo",
                ["Cliente","Fornecedor"],
                default="Cliente",
                selection_mode="single",
            ) or "Cliente"
            name = b.text_input("Nome", placeholder="Nome ou razão social")
            with st.expander("Adicionar detalhes"):
                a, b, d = st.columns(3)
                doc = a.text_input("CPF/CNPJ")
                email = b.text_input("E-mail")
                phone = d.text_input("Telefone")
                notes = st.text_area("Observações")
            save = st.form_submit_button("Salvar contato", type="primary", width="stretch")
            if save:
                document_ok, document_error = cpf_or_cnpj_status(doc)
                if not name.strip():
                    st.error("Informe o nome do contato.")
                elif not document_ok:
                    st.error(document_error)
                else:
                    add_contact(
                        uid, contact_type=typ, name=name.strip(),
                        document=doc.strip(), email=email.strip(),
                        phone=phone.strip(), notes=notes.strip(),
                    )
                    st.rerun()

    with tip_col, st.container(key="rz_panel_contacts_tip"):
        st.caption("ORGANIZAÇÃO")
        st.markdown("**Cadastre só o que você realmente usa.**")
        st.caption("Nome é suficiente para começar; documento e contato podem ser preenchidos depois.")
        st.markdown(
            '<div class="rz-inline-meta"><span>Cliente</span><span>Fornecedor</span></div>',
            unsafe_allow_html=True,
        )

    section("Contatos", "Consulte e gerencie sua lista.")
    if not contacts:
        empty_state(
            "Nenhum cliente ou fornecedor",
            "Adicione seu primeiro contato para organizar quem compra de você e de quem sua empresa compra.",
            "◇",
        )
    else:
        with st.container(key="rz_panel_contacts_list"):
            cdf = pd.DataFrame(contacts)
            professional_table(cdf, max_visible_rows=10)
        with st.expander("Editar contato"):
            edit_cid = st.selectbox(
                "Contato",
                [item["id"] for item in contacts],
                format_func=lambda value: next(item["name"] for item in contacts if item["id"] == value),
                key="editcontact",
            )
            contact_row = next(item for item in contacts if int(item["id"]) == int(edit_cid))
            with st.form("edit_contact_form"):
                a, b = st.columns([1, 2])
                edit_contact_type = a.selectbox(
                    "Tipo",
                    ["Cliente", "Fornecedor"],
                    index=1 if contact_row.get("contact_type") == "Fornecedor" else 0,
                )
                edit_contact_name = b.text_input("Nome", value=str(contact_row.get("name") or ""))
                a, b, d = st.columns(3)
                edit_contact_doc = a.text_input("CPF/CNPJ", value=str(contact_row.get("document") or ""))
                edit_contact_email = b.text_input("E-mail", value=str(contact_row.get("email") or ""))
                edit_contact_phone = d.text_input("Telefone", value=str(contact_row.get("phone") or ""))
                edit_contact_notes = st.text_area("Observações", value=str(contact_row.get("notes") or ""))
                save_contact_edit = st.form_submit_button("Salvar alterações", type="primary", width="stretch")
            if save_contact_edit:
                document_ok, document_error = cpf_or_cnpj_status(edit_contact_doc)
                if not edit_contact_name.strip():
                    st.error("Informe o nome do contato.")
                elif not document_ok:
                    st.error(document_error)
                else:
                    update_contact(
                        uid,
                        int(edit_cid),
                        contact_type=edit_contact_type,
                        name=edit_contact_name.strip(),
                        document=edit_contact_doc.strip(),
                        email=edit_contact_email.strip(),
                        phone=edit_contact_phone.strip(),
                        notes=edit_contact_notes.strip(),
                    )
                    st.rerun()

        with st.expander("Excluir contato"):
            cid = st.selectbox(
                "Selecione",
                [item["id"] for item in contacts],
                format_func=lambda value: next(item["name"] for item in contacts if item["id"] == value),
                key="delcontact",
            )
            st.caption("A exclusão é definitiva.")
            if st.button("Excluir contato selecionado", key="delete_contact_btn", width="stretch"):
                delete_contact(uid, int(cid))
                st.rerun()

elif page == "Empregado":
    header("Empregado", "Mantenha as informações básicas do empregado junto da organização do MEI.")

    active_employees = sum(1 for item in employees if item.get("status") == "Ativo")
    e1, e2 = st.columns(2)
    e1.metric("Cadastrados", len(employees))
    e2.metric("Ativos", active_employees)
    if active_employees >= 1:
        st.info("Pela regra vigente do MEI, mantenha no máximo um empregado ativo. Para substituir, marque o atual como inativo antes de cadastrar outro ativo.")

    with st.container(key="rz_panel_employee_new"):
        st.caption("CADASTRAR EMPREGADO")
        with st.form("emp_form", clear_on_submit=True):
            name = st.text_input("Nome", placeholder="Nome completo")
            a, b = st.columns(2)
            admission = a.date_input("Data de admissão", value=date.today())
            salary = b.number_input("Salário", min_value=0.0, step=50.0)
            with st.expander("Adicionar detalhes"):
                cpf = st.text_input("CPF")
                status = st.selectbox("Situação", ["Ativo","Inativo"])
                notes = st.text_area("Observações")
            save = st.form_submit_button("Salvar empregado", type="primary", width="stretch")
            if save:
                if not name.strip():
                    st.error("Informe o nome do empregado.")
                elif cpf.strip() and not valid_cpf(cpf):
                    st.error("CPF inválido.")
                elif status == "Ativo" and active_employees >= 1:
                    st.error("Já existe um empregado ativo. O MEI pode manter no máximo um empregado ativo pela regra vigente.")
                else:
                    add_employee(
                        uid, name=name.strip(), cpf=cpf.strip(),
                        admission_date=admission, salary=salary,
                        status=status, notes=notes.strip(),
                    )
                    st.rerun()

    section("Empregados cadastrados")
    if not employees:
        empty_state(
            "Nenhum empregado cadastrado",
            "Se o MEI possuir empregado, registre aqui os dados básicos para manter a gestão organizada.",
            "♙",
        )
    else:
        with st.container(key="rz_panel_employee_list"):
            professional_table(pd.DataFrame(employees), max_visible_rows=10)
        with st.expander("Editar empregado"):
            edit_eid = st.selectbox(
                "Empregado",
                [item["id"] for item in employees],
                format_func=lambda value: next(item["name"] for item in employees if item["id"] == value),
                key="editemp",
            )
            employee_row = next(item for item in employees if int(item["id"]) == int(edit_eid))
            raw_admission = employee_row.get("admission_date")
            if isinstance(raw_admission, str):
                try:
                    raw_admission = date.fromisoformat(raw_admission[:10])
                except ValueError:
                    raw_admission = date.today()
            if not isinstance(raw_admission, date):
                raw_admission = date.today()
            with st.form("edit_employee_form"):
                edit_employee_name = st.text_input("Nome", value=str(employee_row.get("name") or ""))
                a, b = st.columns(2)
                edit_employee_admission = a.date_input("Data de admissão", value=raw_admission)
                edit_employee_salary = b.number_input(
                    "Salário",
                    min_value=0.0,
                    value=float(employee_row.get("salary") or 0),
                    step=50.0,
                )
                a, b = st.columns(2)
                edit_employee_cpf = a.text_input("CPF", value=str(employee_row.get("cpf") or ""))
                current_employee_status = str(employee_row.get("status") or "Ativo")
                edit_employee_status = b.selectbox(
                    "Situação",
                    ["Ativo", "Inativo"],
                    index=1 if current_employee_status == "Inativo" else 0,
                )
                edit_employee_notes = st.text_area("Observações", value=str(employee_row.get("notes") or ""))
                save_employee_edit = st.form_submit_button("Salvar alterações", type="primary", width="stretch")
            if save_employee_edit:
                other_active = sum(
                    1 for item in employees
                    if int(item["id"]) != int(edit_eid) and item.get("status") == "Ativo"
                )
                if not edit_employee_name.strip():
                    st.error("Informe o nome do empregado.")
                elif edit_employee_cpf.strip() and not valid_cpf(edit_employee_cpf):
                    st.error("CPF inválido.")
                elif edit_employee_status == "Ativo" and other_active >= 1:
                    st.error("Já existe outro empregado ativo. O MEI pode manter no máximo um empregado ativo pela regra vigente.")
                else:
                    update_employee(
                        uid,
                        int(edit_eid),
                        name=edit_employee_name.strip(),
                        cpf=edit_employee_cpf.strip(),
                        admission_date=edit_employee_admission,
                        salary=edit_employee_salary,
                        status=edit_employee_status,
                        notes=edit_employee_notes.strip(),
                    )
                    st.rerun()

        with st.expander("Excluir empregado"):
            eid = st.selectbox(
                "Selecione",
                [item["id"] for item in employees],
                format_func=lambda value: next(item["name"] for item in employees if item["id"] == value),
                key="delemp",
            )
            st.caption("A exclusão é definitiva.")
            if st.button("Excluir empregado selecionado", key="delete_employee_btn", width="stretch"):
                delete_employee(uid, int(eid))
                st.rerun()

elif page == "Documentos":
    header("Documentos", "Guarde o essencial sem transformar a tela em um arquivo cheio de controles.")

    d1, d2, d3 = st.columns(3)
    with d1:
        stat_card("Arquivos", str(len(docs)), detail="salvos")
    with d2:
        stat_card(
            "Tipos",
            str(len({str(item.get("category") or "") for item in docs if item.get("category")})),
            detail="em uso",
        )
    with d3:
        stat_card(
            "Competências",
            str(len({str(item.get("reference_month") or "") for item in docs if item.get("reference_month")})),
            detail="organizadas",
        )

    upload_col, helper_col = st.columns([1.7, .8], gap="large")
    with upload_col:
        st.markdown("#### Adicionar arquivo")
        up = st.file_uploader(
            "PDF ou imagem",
            type=["pdf", "png", "jpg", "jpeg"],
            key="docup",
            label_visibility="collapsed",
        )
        suggestion = None
        if up is not None:
            with st.spinner("Analisando..."):
                suggestion = cached_document_analysis(
                    up.getvalue(),
                    up.type or "",
                    up.name,
                )

            st.caption("SUGESTÃO DO RAZYNC")
            s1, s2, s3 = st.columns(3)
            s1.metric("Tipo", suggestion["category"])
            s2.metric("Competência", suggestion["reference_month"] or "—")
            s3.metric("Confiança", suggestion["confidence"])

            if suggestion["warning"]:
                st.info(suggestion["warning"])
            if suggestion["text_preview"]:
                with st.expander("Trecho reconhecido"):
                    st.text(suggestion["text_preview"])

        suggested_category = suggestion["category"] if suggestion else "Nota Fiscal"
        suggested_reference = suggestion["reference_month"] if suggestion else ""
        a, b = st.columns(2)
        category = a.selectbox(
            "Tipo",
            DOCUMENT_CATEGORIES,
            index=DOCUMENT_CATEGORIES.index(suggested_category),
            key=f"doc_category_{up.name if up else 'empty'}",
        )
        reference = b.text_input(
            "Competência",
            value=suggested_reference,
            placeholder="AAAA-MM",
            key=f"doc_reference_{up.name if up else 'empty'}",
        )
        valid_reference = not reference.strip() or valid_competence(reference.strip())
        if not valid_reference:
            st.warning("Use AAAA-MM. Ex.: 2026-08.")

        if st.button(
            "Salvar documento",
            type="primary",
            disabled=up is None or not valid_reference,
        ):
            if up:
                try:
                    save_uploaded_document(
                        user,
                        up,
                        category,
                        reference.strip(),
                    )
                except Exception:
                    st.error("Não foi possível armazenar o documento agora.")
                else:
                    st.rerun()

    with helper_col:
        st.markdown("#### Organização")
        st.caption(
            "A competência é o que mais ajuda depois. O tipo pode ser ajustado antes de salvar."
        )
        st.write("• Nota fiscal")
        st.write("• DAS")
        st.write("• Extrato")
        st.write("• Comprovante")
        st.write("• Outros")
        st.caption("O Razync sugere. Você confirma.")

    st.markdown("#### Biblioteca")
    if not docs:
        empty_state(
            "Nenhum documento salvo",
            "Adicione os arquivos que realmente ajudam no fechamento e na conferência.",
            "▱",
        )
    else:
        ddf = pd.DataFrame(docs)
        visible_columns = [
            column
            for column in ["filename", "category", "reference_month", "created_at"]
            if column in ddf.columns
        ]
        professional_table(
            ddf[visible_columns],
            max_visible_rows=10,
        )

        manage_col, action_col = st.columns([1.7, .8], gap="large")
        with manage_col:
            did = st.selectbox(
                "Selecionar documento",
                [d["id"] for d in docs],
                format_func=lambda x: next(d["filename"] for d in docs if d["id"] == x),
            )
            selected_meta = next(
                d for d in docs if int(d["id"]) == int(did)
            )
            st.caption(
                f"{selected_meta.get('category') or 'Sem tipo'} · "
                f"{selected_meta.get('reference_month') or 'Sem competência'}"
            )

        with action_col:
            prepared_key = f"_prepared_document_{uid}_{int(did)}"
            if st.button(
                "Preparar download",
                key=f"prepare_doc_{did}",
                type="primary",
                width="stretch",
            ):
                try:
                    selected = get_document(uid, int(did))
                    if not selected:
                        raise RuntimeError("Documento não encontrado")
                    content_bytes = document_bytes(selected)
                except Exception:
                    st.error("Não foi possível preparar o arquivo.")
                else:
                    st.session_state[prepared_key] = {
                        "content": content_bytes,
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

        with st.expander("Gerenciar biblioteca"):
            tab_coverage, tab_delete = st.tabs(["Cobertura", "Excluir"])
            with tab_coverage:
                coverage = document_coverage(docs, CURRENT_YEAR)
                professional_table(coverage, max_visible_rows=12)
            with tab_delete:
                st.caption("A exclusão remove o arquivo armazenado no Razync.")
                if st.button(
                    "Excluir documento selecionado",
                    key="delete_document_btn",
                ):
                    try:
                        remove_saved_document(uid, selected_meta)
                    except Exception:
                        st.error("Não foi possível excluir o documento agora.")
                    else:
                        st.session_state.pop(prepared_key, None)
                        st.rerun()

elif page == "Espaço do Contador":
    header("Espaço do Contador", "Prepare relatórios e arquivos para compartilhar sem liberar senhas.")

    a, b = st.columns(2)
    accountant_year = a.selectbox(
        "Ano de referência",
        list(range(CURRENT_YEAR - 4, CURRENT_YEAR + 1)),
        index=4,
        key="accountant_year",
    )
    accountant_month = b.selectbox(
        "Mês de referência",
        list(range(1, 13)),
        index=date.today().month - 1,
        format_func=lambda value: MONTH_NAMES_PT[value - 1],
        key="accountant_month",
    )

    analysis_data = financial_analysis(transactions, accountant_year)
    accountant_closing = monthly_closing(
        transactions, invoices, docs, das_rows,
        accountant_year, accountant_month,
    )
    summary_pdf = cached_financial_summary_pdf(profile, accountant_year, analysis_data)
    closing_pdf = cached_closing_summary_pdf(
        profile, accountant_year, accountant_month, accountant_closing
    )

    with st.container(key="rz_panel_accountant_package"):
        st.caption("PACOTE PARA O CONTADOR")
        p1, p2 = st.columns(2)
        p1.download_button(
            "Baixar resumo financeiro",
            summary_pdf,
            file_name=f"resumo_contador_{accountant_year}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        p2.download_button(
            "Baixar fechamento do mês",
            closing_pdf,
            file_name=f"fechamento_{accountant_year}_{accountant_month:02d}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.caption("Compartilhe apenas os arquivos necessários. Senhas de banco, gov.br e Razync não devem ser enviadas.")

    if st.button("Preparar backup completo", key="accountant_backup", width="stretch"):
        st.session_state["_navigate_to"] = "Backup"
        st.rerun()

elif page == "Central de Automações":
    header("Automações", "Revise prioridades, previsões e tarefas assistidas sem perder o controle das decisões.")
    automation = automation_overview(
        profile, transactions, invoices, das_rows, obligations, docs,
        CURRENT_YEAR, date.today().month,
    )
    closing = automation["closing"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fechamento", f"{closing['score']}%")
    c2.metric("Conciliações", len(automation["invoice_matches"]))
    c3.metric("DAS encontrados", len(automation["das_matches"]))
    c4.metric("Sem documento", automation["documents"]["missing_count"])

    priorities = automation["action_items"][:5]
    if priorities:
        section("O que merece atenção agora", "Abra direto a rotina certa para resolver.")
        with st.container(key="rz_panel_automation_priorities"):
            for idx, item in enumerate(priorities):
                level = (
                    "danger" if item["priority"] == 1
                    else "warn" if item["priority"] == 2
                    else "info" if item["priority"] == 3
                    else "ok"
                )
                alert_card(level, item["title"], item["detail"])
                if item["page"] and st.button(
                    "Abrir rotina",
                    key=f"automation_action_{idx}",
                    width="stretch",
                ):
                    st.session_state["_navigate_to"] = item["page"]
                    st.rerun()
    else:
        st.success("Nenhuma prioridade importante identificada agora.")

    closing_tab, review_tab, forecast_tab, share_tab = st.tabs([
        "Fechamento", "Revisões", "Previsão", "Compartilhar"
    ])

    with closing_tab:
        st.caption(f"Fechamento de {date.today().month:02d}/{CURRENT_YEAR}")
        st.progress(closing["score"] / 100)
        professional_table(pd.DataFrame(closing["checklist"]), max_visible_rows=7)
        if st.button("Abrir fechamento mensal", key="automation_closing", width="stretch"):
            st.session_state["_navigate_to"] = "Fechamento Mensal"
            st.rerun()

    with review_tab:
        st.markdown("##### Possíveis pagamentos de DAS")
        if automation["das_matches"]:
            professional_table(pd.DataFrame(automation["das_matches"]), max_visible_rows=7)
            st.caption("O Razync apenas sugere. Confirme o pagamento na página DAS.")
        else:
            st.success("Nenhum possível pagamento aguardando revisão.")

        st.markdown("##### Despesas fora do padrão")
        if automation["anomalies"]:
            anomaly_df = pd.DataFrame(automation["anomalies"]).rename(columns={
                "description": "Descrição",
                "category": "Categoria",
                "value": "Valor",
                "reference": "Mediana",
            })
            professional_table(
                anomaly_df,
                max_visible_rows=7,
                column_config={
                    "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Mediana": st.column_config.NumberColumn(format="R$ %.2f"),
                },
            )
        else:
            st.success("Nenhuma despesa fora do padrão identificada.")

        if st.button("Abrir conciliação", key="automation_reconcile", width="stretch"):
            st.session_state["_navigate_to"] = "Conciliação"
            st.rerun()

    with forecast_tab:
        st.caption("Projeção baseada nos meses recentes que possuem movimentações cadastradas. Não representa saldo bancário.")
        professional_table(
            automation["forecast"],
            max_visible_rows=6,
            column_config={
                "Receitas previstas": st.column_config.NumberColumn(format="R$ %.2f"),
                "Despesas previstas": st.column_config.NumberColumn(format="R$ %.2f"),
                "Resultado acumulado projetado": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )
        projected = automation["forecast"]
        if not projected.empty and float(projected.iloc[-1]["Resultado acumulado projetado"]) < 0:
            st.error("A projeção indica resultado acumulado negativo. Revise despesas e recebimentos previstos.")
        else:
            st.success("A projeção atual não indica resultado acumulado negativo nos próximos três meses.")

    with share_tab:
        reminders = automation["reminders"]
        st.markdown("##### Lembretes de recebimento")
        if not reminders:
            st.success("Nenhuma nota emitida está aguardando conciliação com recebimento.")
        else:
            reminder_labels = {
                item["invoice_id"]: f"Nota {item['number'] or item['invoice_id']} · {item['customer']} · {brl(item['amount'])}"
                for item in reminders
            }
            reminder_id = st.selectbox(
                "Nota",
                list(reminder_labels),
                format_func=lambda value: reminder_labels[value],
            )
            reminder = next(item for item in reminders if item["invoice_id"] == reminder_id)
            st.text_area("Mensagem preparada", value=reminder["message"], height=120)
            r1, r2 = st.columns(2)
            r1.link_button("Abrir no WhatsApp", reminder["whatsapp_url"], width="stretch")
            r2.link_button("Abrir no e-mail", reminder["email_url"], width="stretch")
            st.caption("Nada é enviado automaticamente. Revise antes de enviar.")

        p1, p2 = st.columns(2)
        if p1.button("Espaço do Contador", width="stretch"):
            st.session_state["_navigate_to"] = "Espaço do Contador"
            st.rerun()
        if p2.button("Preparar backup", width="stretch"):
            st.session_state["_navigate_to"] = "Backup"
            st.rerun()

elif page == "Assistente Razync":
    from assistant_workspace import render_ai_assistant

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
    header("Primeiros Passos", "Configure o essencial e deixe o Razync útil desde os primeiros minutos.")
    progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))

    p1, p2 = st.columns([1, 2.2])
    with p1:
        st.metric("Configuração", f"{progress['percent']}%")
    with p2:
        st.caption(f"{progress['done']} de {progress['total']} etapas concluídas")
        st.progress(progress["percent"] / 100)

    next_step = next_onboarding_step(progress)
    if next_step:
        with st.container(key="rz_panel_onboarding_next"):
            st.caption("PRÓXIMO PASSO")
            st.markdown(f"**{next_step['action']}**")
            st.caption(next_step["detail"])
            if next_step["page"] != "Primeiros Passos" and st.button(
                next_step["action"],
                key="onboarding_next_action",
                type="primary",
                width="stretch",
            ):
                st.session_state["_navigate_to"] = next_step["page"]
                st.rerun()
    else:
        st.success("Configuração inicial concluída.")

    with st.container(key="rz_panel_onboarding_profile"):
        st.caption("DADOS ESSENCIAIS")
        with st.form("onboarding_profile"):
            a, b = st.columns(2)
            business_name = a.text_input(
                "Nome do negócio",
                value=str(profile.get("trade_name") or profile.get("business_name") or ""),
            )
            cnpj = b.text_input("CNPJ", value=str(profile.get("cnpj") or ""))
            a, b = st.columns(2)
            main_activity = a.text_input(
                "Atividade principal",
                value=str(profile.get("main_activity") or ""),
                placeholder="Ex.: design gráfico, comércio de roupas",
            )
            activity_options = ["Serviços","Comércio","Indústria","Misto"]
            current_activity = (
                profile.get("activity_type")
                if profile.get("activity_type") in activity_options
                else "Serviços"
            )
            activity_type = b.selectbox(
                "Tipo de atividade",
                activity_options,
                index=activity_options.index(current_activity),
            )
            opening_date = st.date_input("Data de abertura", value=opening or date.today())
            if st.form_submit_button("Salvar dados básicos", type="primary", width="stretch"):
                if cnpj.strip() and not valid_cnpj(cnpj):
                    st.error("CNPJ inválido. Confira os 14 dígitos.")
                else:
                    save_profile(
                        uid,
                        business_name=business_name,
                        trade_name=business_name,
                        cnpj=cnpj,
                        main_activity=main_activity,
                        activity_type=activity_type,
                        opening_date=opening_date,
                    )
                    st.rerun()

    section("Roteiro inicial", "Conclua apenas o que ainda estiver pendente.")
    step_cards = []
    for step in progress["steps"]:
        state_class = "is-done" if step["done"] else "is-pending"
        state_label = "Concluído" if step["done"] else "Pendente"
        step_cards.append(
            f'<div class="rz-status-step {state_class}"><strong>{escape(step["title"])}</strong>'
            f'<span>{state_label} · {escape(step["detail"])}</span></div>'
        )
    st.markdown(
        '<div class="rz-status-grid">' + "".join(step_cards) + "</div>",
        unsafe_allow_html=True,
    )

    a, b, d = st.columns(3)
    if a.button("Registrar movimentação", width="stretch"):
        st.session_state["_navigate_to"] = "Movimentações"
        st.rerun()
    if b.button("Configurar DAS", width="stretch"):
        st.session_state["_navigate_to"] = "DAS"
        st.rerun()
    if d.button("Adicionar documento", width="stretch"):
        st.session_state["_navigate_to"] = "Documentos"
        st.rerun()

    with st.expander("Recomendações do Razync"):
        for tip in recommended_setup(profile):
            helper_note(tip)

elif page == "Meu MEI":
    header("Meu MEI", "Mantenha os dados que alimentam alertas, relatórios e documentos do Razync.")

    essential_values = [
        profile.get("cnpj"), profile.get("business_name") or profile.get("trade_name"),
        profile.get("main_activity"), profile.get("opening_date"),
    ]
    completed = sum(bool(value) for value in essential_values)
    p1, p2, p3 = st.columns(3)
    p1.metric("Dados essenciais", f"{completed}/4")
    p2.metric("Tipo de atividade", profile.get("activity_type") or "Não definido")
    p3.metric("Município", profile.get("city") or "Não definido")

    with st.container(key="rz_panel_mei_profile"):
        st.caption("DADOS DO NEGÓCIO")
        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            cnpj = c1.text_input("CNPJ", value=str(profile.get("cnpj") or ""))
            opening_date = c2.date_input("Data de abertura", value=opening or date.today())

            c1, c2 = st.columns(2)
            business = c1.text_input("Razão social", value=str(profile.get("business_name") or ""))
            trade = c2.text_input("Nome fantasia", value=str(profile.get("trade_name") or ""))

            activity = st.text_input("Atividade principal", value=str(profile.get("main_activity") or ""))
            c1, c2 = st.columns(2)
            activity_types = ["Serviços","Comércio","Indústria","Misto"]
            activity_type = c1.selectbox(
                "Tipo de atividade",
                activity_types,
                index=activity_types.index(profile.get("activity_type")) if profile.get("activity_type") in activity_types else 0,
            )
            annual_limit = c2.number_input(
                "Limite anual monitorado",
                min_value=0.0,
                value=float(profile.get("annual_limit") or MEI_ANNUAL_LIMIT),
                step=1000.0,
            )

            with st.expander("Endereço e contato"):
                c1, c2 = st.columns([2, 1])
                city = c1.text_input("Município", value=str(profile.get("city") or ""))
                state = c2.text_input("UF", value=str(profile.get("state") or ""), max_chars=2)
                phone = st.text_input("Telefone", value=str(profile.get("phone") or ""))

            with st.expander("Inscrições e empregado"):
                c1, c2 = st.columns(2)
                municipal = c1.text_input("Inscrição municipal", value=str(profile.get("municipal_registration") or ""))
                state_reg = c2.text_input("Inscrição estadual", value=str(profile.get("state_registration") or ""))
                has_employee = st.checkbox("Possui empregado", value=bool(profile.get("has_employee", False)))

            if st.form_submit_button("Salvar dados do MEI", type="primary", width="stretch"):
                if cnpj.strip() and not valid_cnpj(cnpj):
                    st.error("CNPJ inválido. Confira os 14 dígitos antes de salvar.")
                else:
                    save_profile(
                        uid, cnpj=cnpj, business_name=business, trade_name=trade,
                        main_activity=activity, activity_type=activity_type,
                        opening_date=opening_date, annual_limit=annual_limit,
                        city=city, state=state.upper(), phone=phone,
                        municipal_registration=municipal,
                        state_registration=state_reg, has_employee=has_employee,
                    )
                    st.success("Dados salvos.")
                    st.rerun()

elif page == "Central de Notificações":
    header("Alertas e Calendário", "Veja somente o que exige atenção e leve os prazos importantes para seu calendário.")
    automatic_reminders = upcoming_automatic_obligations(
        CURRENT_YEAR,
        opening,
        das_rows,
        today=date.today(),
        days_ahead=90,
    )
    notification_items = build_notifications(
        das_rows,
        [*obligations, *automatic_reminders],
        year_revenue,
        limit,
        today=date.today(),
    )
    urgent_count = sum(1 for item in notification_items if item.get("level") == "urgent")

    n1, n2 = st.columns(2)
    n1.metric("Alertas ativos", len(notification_items))
    n2.metric("Urgentes", urgent_count)

    if not notification_items:
        st.success("Nenhum alerta importante identificado agora.")
    else:
        with st.container(key="rz_panel_notifications"):
            for idx, item in enumerate(notification_items):
                level = "danger" if item["level"] == "urgent" else "warn"
                if st.button(
                    f"**{item['title']}**\n\n{item['detail']}\n\nResolver agora →",
                    key=f"rz_action_card_{level}_notification_{idx}",
                    width="stretch",
                ):
                    st.session_state["_navigate_to"] = item["page"]
                    st.rerun()

        app_url = secret_value("APP_URL") or "https://razync-pro-production.up.railway.app/"
        calendar_file = notification_calendar(notification_items, app_url)
        st.download_button(
            "Adicionar prazos ao calendário (.ics)",
            calendar_file,
            file_name="agenda_razync_mei.ics",
            mime="text/calendar",
            width="stretch",
        )
    st.caption("Os alertas combinam dados cadastrados e prazos automáticos futuros. Confirme datas e valores nos documentos oficiais.")

elif page == "Integrações":
    header("Integrações", "Entenda o que já está conectado, o que é assistido e o que depende de terceiros.")
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
    i3.metric("Com confirmação", len(catalog) - automatic_count)

    section("Conexões", "Nenhuma integração envia dados ou mensagens sem autorização.")
    left, right = st.columns(2, gap="large")
    for idx, item in enumerate(catalog):
        target = left if idx % 2 == 0 else right
        with target, st.container(key=f"rz_panel_integration_{idx}"):
            st.caption(item["mode"].upper())
            st.markdown(f"**{item['name']}**")
            st.caption(f"{integration_maturity(item)} · {item['status']}")
            st.write(item["detail"])
            if item["page"] and st.button("Abrir recurso", key=f"integration_page_{idx}", width="stretch"):
                st.session_state["_navigate_to"] = item["page"]
                st.rerun()
            if item["name"] == "DAS do MEI":
                st.link_button("Abrir portal oficial", OFFICIAL_SERVICES["das"]["url"], width="stretch")
            elif item["name"] == "NFS-e Nacional":
                st.link_button("Abrir emissor oficial", OFFICIAL_SERVICES["nfse"]["url"], width="stretch")

    st.info("Open Finance e WhatsApp automático dependem de provedores externos e consentimento. A importação manual continua disponível sem essas integrações.")

elif page == "Plano e Assinatura":
    header("Planos e Recursos", "Compare o que o Razync pretende oferecer quando o acesso comercial for reativado.")

    if st.session_state.get("auth_provider") == "public":
        st.info("O ambiente atual está em modo de desenvolvimento com acesso direto. Não existe assinatura individual ativa neste momento.")

    p1, p2 = st.columns(2, gap="large")
    for column, plan_name in zip((p1, p2), ("Essencial", "Pro")):
        plan = PLAN_CATALOG[plan_name]
        with column, st.container(key=f"rz_panel_plan_{plan_name.lower()}"):
            st.caption(f"PLANO {plan_name.upper()}")
            st.markdown(f"### Razync {plan_name}")
            st.caption(plan["description"])
            for feature in plan["features"]:
                st.write(f"✓ {feature}")

    config = {"CHECKOUT_PRO_URL": secret_value("CHECKOUT_PRO_URL")}
    payment_url = checkout_url(config, "pro")
    if st.session_state.get("auth_provider") != "public" and payment_url:
        st.link_button("Assinar Razync Pro", payment_url, type="primary", width="stretch")
        st.caption("O pagamento é processado pelo provedor configurado; dados de cartão não passam pelo Razync.")
    else:
        st.caption("Checkout e cobrança permanecem desativados enquanto o sistema estiver em acesso direto.")

elif page == "Histórico de Atividades":
    header("Histórico de Atividades", "Consulte inclusões, alterações e exclusões registradas pelo Razync.")
    audit_rows = list_audit_logs(uid, 250)

    if not audit_rows:
        empty_state(
            "Nenhuma atividade registrada",
            "As próximas inclusões, alterações e exclusões aparecerão aqui.",
            "◷",
        )
    else:
        action_labels = {"INSERT":"Criado","UPDATE":"Alterado","DELETE":"Excluído"}
        module_labels = {
            "transactions":"Movimentações",
            "das_items":"DAS",
            "documents":"Documentos",
            "invoices":"Notas fiscais",
            "contacts":"Contatos",
            "employees":"Empregado",
            "obligations":"Obrigações",
            "recurring_transactions":"Recorrências",
            "mei_profiles":"Meu MEI",
        }
        audit_view = pd.DataFrame([
            {
                "Data": row.get("created_at"),
                "Módulo": module_labels.get(row.get("table_name"), row.get("table_name")),
                "Ação": action_labels.get(row.get("action"), row.get("action")),
                "Registro": row.get("record_id") or "—",
            }
            for row in audit_rows
        ])
        h1, h2 = st.columns([1.2, 2])
        filter_module = h1.selectbox(
            "Módulo",
            ["Todos"] + sorted(audit_view["Módulo"].dropna().unique().tolist()),
        )
        h2.caption(f"{len(audit_rows)} evento(s) mais recentes registrados")
        if filter_module != "Todos":
            audit_view = audit_view[audit_view["Módulo"] == filter_module]

        with st.container(key="rz_panel_audit_history"):
            professional_table(
                audit_view,
                max_visible_rows=12,
                column_config={"Data": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")},
            )
        st.caption("Senhas e conteúdo binário de documentos nunca são incluídos no histórico.")

elif page == "Status do Sistema":
    header("Status do Sistema", "Veja a infraestrutura ativa do Razync Pro e o que ainda é provisório.")
    runtime = database_runtime_info()
    backend_name = str(runtime.get("backend") or "")
    postgres_ready = "postgres" in backend_name.lower()

    s1, s2, s3 = st.columns(3)
    s1.metric("Hospedagem", "Railway")
    s2.metric("Persistência", "Ativa" if runtime["persistent"] else "Revisar")
    s3.metric("Modo de acesso", "Direto")

    with st.container(key="rz_panel_system_runtime"):
        st.caption("INFRAESTRUTURA")
        st.write(f"**Banco atual:** {backend_name or 'não identificado'}")
        st.write("**Servidor:** Railway")
        st.write("**Sleep do serviço:** desativado")
        st.write(f"**Persistência do workspace:** {'ativa' if runtime['persistent'] else 'revisar'}")
        if runtime["persistent"]:
            st.success("Os dados operacionais atuais estão em armazenamento persistente.")
        else:
            st.warning("A persistência precisa ser revisada antes de armazenar dados reais de clientes.")

    status_config = {
        key: secret_value(key)
        for key in ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "CHECKOUT_PRO_URL")
    }
    with st.expander("Integrações e prontidão"):
        for integration in integration_readiness(status_config, runtime["persistent"]):
            marker = "✓" if integration["ready"] else "○"
            st.write(f"{marker} **{integration['name']}** — {integration['detail']}")
        st.write("✓ **Importação bancária por arquivo** — disponível")
        st.write("○ **Autenticação de usuários** — temporariamente desativada por decisão de desenvolvimento")
        st.write(
            f"{'✓' if postgres_ready else '○'} **PostgreSQL definitivo** — "
            + ("conectado" if postgres_ready else "conectar antes de reativar contas comerciais")
        )

elif page == "Backup":
    header("Backup", "Gere uma cópia independente dos dados e documentos do Razync.")
    backup_key = f"_prepared_backup_{uid}_{_current_data_version}"

    with st.container(key="rz_panel_backup"):
        st.caption("CÓPIA COMPLETA")
        st.markdown("**Seus dados só são reunidos quando você solicitar.**")
        st.caption("Isso evita carregar documentos desnecessariamente durante a navegação normal.")
        if st.button("Preparar backup completo", type="primary", width="stretch"):
            with st.spinner("Preparando backup..."):
                backup = build_backup_zip(
                    profile, transactions, invoices, das_rows, obligations,
                    contacts, employees, docs,
                    lambda doc_id: (
                        lambda d: {**d, "content": document_bytes(d)} if d else None
                    )(get_document(uid, doc_id)),
                )
                st.session_state[backup_key] = backup

    backup = st.session_state.get(backup_key)
    if backup:
        st.success("Backup preparado.")
        st.download_button(
            "Baixar backup completo (.zip)",
            backup,
            file_name=f"backup_razync_{date.today().isoformat()}.zip",
            mime="application/zip",
            width="stretch",
        )
        with st.expander("Código de integridade"):
            st.code(backup_checksum(backup), language=None)
            st.caption("Guarde este código junto do arquivo para verificar se o backup foi alterado.")
st.divider()
st.caption("Razync Pro • Ecossistema Razync • ferramenta de organização contábil e financeira para MEI")
