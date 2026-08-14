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
    update_obligation_status, update_transaction, upsert_das, link_transaction_document,
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
from backup_tools import backup_checksum, build_backup_zip, document_coverage
from onboarding_tools import onboarding_progress, recommended_setup
from reconciliation_tools import smart_invoice_matches, duplicate_groups
from ui_system import inject_design_system, page_header, section, business_card, alert_card, empty_state, helper_note, apply_plot_theme, tokens
from login_security import login_attempt_guard
from storage_service import download_document, remove_document, upload_document
from auth_service import (
    AuthServiceError, is_supabase_auth_configured, reset_password,
    restore_session as supabase_restore_session,
    sign_in as supabase_sign_in, sign_out as supabase_sign_out,
    sign_up as supabase_sign_up, update_password as supabase_update_password,
)
from session_persistence import (
    clear_persisted_session, persist_refresh_token,
    persistent_session_controller, read_refresh_token,
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

    if "user" in st.session_state:
        user = st.session_state["user"]
        with st.sidebar:
            st.caption(f"Conectado como {user['name']}")
            if st.button("Sair", use_container_width=True):
                clear_persisted_session(session_controller)
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
            keep_connected = st.checkbox(
                "Manter conectado neste dispositivo",
                value=True,
                disabled=session_controller is None,
                help="Sua sessão é renovada pelo Supabase e removida ao sair.",
            )
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
year_revenue = float(y…8699 tokens truncated…AS controlado neste ano", "Adicione uma competência para acompanhar vencimento e pagamento do DAS dentro do Razync.", "▣")
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

elif page == "Segurança da Conta":
    header("Segurança da Conta", "Atualize sua senha e confira como sua sessão é protegida.")
    with st.container(border=True):
        st.subheader("Alterar senha")
        with st.form("change_password_form", clear_on_submit=True):
            new_password = st.text_input("Nova senha", type="password", help="Use pelo menos 8 caracteres.")
            password_confirmation = st.text_input("Confirmar nova senha", type="password")
            change_password = st.form_submit_button("Alterar senha", type="primary", use_container_width=True)
        if change_password:
            if new_password != password_confirmation:
                st.error("As senhas não coincidem.")
            elif len(new_password) < 8:
                st.error("A nova senha deve ter pelo menos 8 caracteres.")
            elif not is_supabase_auth_configured():
                st.error("A alteração de senha requer o Supabase Auth.")
            else:
                try:
                    supabase_update_password(
                        st.session_state.get("access_token", ""),
                        st.session_state.get("refresh_token", ""),
                        new_password,
                    )
                except AuthServiceError as exc:
                    st.error(str(exc))
                else:
                    st.success("Senha alterada com sucesso.")
    section("Sessão e privacidade")
    st.write("✓ A opção **Manter conectado** armazena somente um token de renovação criptografado.")
    st.write("✓ Ao sair, a sessão local e o token persistente são removidos.")
    st.write("✓ Os dados de cada conta são isolados pelo usuário autenticado.")
    st.info("Em dispositivo compartilhado, use sempre o botão Sair ao terminar.")

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
    st.caption("O pacote inclui dados em CSV/JSON, manifesto e os documentos disponíveis no Razync Pro.")
    st.code(backup_checksum(backup), language=None)
    st.caption("Guarde este código de integridade junto do arquivo para conferir se o backup não foi alterado.")

st.divider()
st.caption("Razync Pro • Ecossistema Razync • ferramenta de organização contábil e financeira para MEI")
