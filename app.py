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

CURRENT_YEAR = date.today().year
MEI_ANNUAL_LIMIT_2026 = 81000.0
MEI_MONTHLY_PROPORTION = 6750.0

st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
:root { --rz-blue:#2563eb; --rz-blue2:#60a5fa; --rz-dark:#050914; --rz-card:#0b1220; --rz-border:#1f2a3d; }
.stApp { background:radial-gradient(circle at 12% 0%, #0b1832 0%, #050914 36%, #050914 100%); }
[data-testid="stSidebar"] { background:#070c16; border-right:1px solid #172236; }
[data-testid="stMetric"] { background:linear-gradient(180deg,rgba(17,28,49,.96),rgba(9,16,29,.96)); border:1px solid #1d2a42; border-radius:16px; padding:14px 16px; }
.block-container { padding-top:1.1rem; padding-bottom:2rem; max-width:1500px; }
.rz-brand { font-size:1.55rem; font-weight:900; letter-spacing:-.04em; }
.rz-brand span { color:#60a5fa; }
.rz-kicker { color:#60a5fa; font-weight:800; text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; }
.rz-title { font-size:2rem; font-weight:900; margin:.15rem 0 .2rem; letter-spacing:-.035em; }
.rz-sub { color:#94a3b8; margin-bottom:1.2rem; }
.rz-alert { border-radius:14px; padding:12px 14px; margin-bottom:9px; background:#0b1425; border:1px solid #1f2d45; }
.rz-ok { border-left:4px solid #22c55e; }.rz-warn { border-left:4px solid #f59e0b; }.rz-danger { border-left:4px solid #ef4444; }
.rz-small { color:#94a3b8; font-size:.88rem; }
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button { border-radius:10px; }
div[data-testid="stDataFrame"] { border:1px solid #1c2940; border-radius:12px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def header(title: str, subtitle: str) -> None:
    st.markdown('<div class="rz-kicker">Razync Pro • MEI</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-sub">{subtitle}</div>', unsafe_allow_html=True)


def ensure_login() -> dict:
    if "user" in st.session_state:
        return st.session_state.user
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)
        st.caption("Contabilidade simples, funcional e moderna para MEI")
        login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("E-mail")
                password = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                    user = authenticate(email, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    st.error("E-mail ou senha inválidos.")
        with register_tab:
            with st.form("register_form"):
                name = st.text_input("Nome")
                email = st.text_input("E-mail", key="reg_email")
                p1 = st.text_input("Senha", type="password", key="reg_p1")
                p2 = st.text_input("Confirmar senha", type="password")
                if st.form_submit_button("Criar conta", type="primary", use_container_width=True):
                    if len(p1) < 8:
                        st.error("Use uma senha com pelo menos 8 caracteres.")
                    elif p1 != p2:
                        st.error("As senhas não coincidem.")
                    elif not name.strip() or "@" not in email:
                        st.error("Preencha nome e e-mail válidos.")
                    else:
                        ok, msg = create_user(name, email, p1)
                        st.success(msg) if ok else st.error(msg)
    st.stop()


def tx_df(user_id: int) -> pd.DataFrame:
    df = pd.DataFrame(list_transactions(user_id))
    if df.empty:
        return pd.DataFrame(columns=["id","tx_date","tx_type","description","category","value","document_number","counterparty","payment_method"])
    df["tx_date"] = pd.to_datetime(df["tx_date"])
    return df


def invoices_df(user_id: int) -> pd.DataFrame:
    df = pd.DataFrame(list_invoices(user_id))
    if not df.empty:
        df["issue_date"] = pd.to_datetime(df["issue_date"])
    return df


def annual_limit(profile: dict) -> float:
    try:
        opening = profile.get("opening_date")
        if not opening:
            return MEI_ANNUAL_LIMIT_2026
        if isinstance(opening, str):
            opening = date.fromisoformat(opening)
        if opening.year == CURRENT_YEAR:
            return MEI_MONTHLY_PROPORTION * (13 - opening.month)
    except Exception:
        pass
    configured = float(profile.get("annual_limit") or 0)
    return configured if configured > 0 else MEI_ANNUAL_LIMIT_2026


def monthly_revenue_breakdown(df: pd.DataFrame, year: int) -> pd.DataFrame:
    months = pd.DataFrame({"month": range(1,13)})
    if df.empty:
        months["receita"] = 0.0
        return months
    r = df[(df["tx_type"]=="Receita") & (df["tx_date"].dt.year==year)].copy()
    if r.empty:
        months["receita"] = 0.0
        return months
    grp = r.groupby(r["tx_date"].dt.month)["value"].sum().rename("receita").reset_index().rename(columns={"tx_date":"month"})
    return months.merge(grp, on="month", how="left").fillna({"receita":0})


def alert_box(text: str, level: str="ok") -> None:
    cls = {"ok":"rz-ok","warn":"rz-warn","danger":"rz-danger"}.get(level,"rz-ok")
    st.markdown(f'<div class="rz-alert {cls}">{text}</div>', unsafe_allow_html=True)


user = ensure_login()
uid = int(user["id"])
profile = get_profile(uid)
transactions = tx_df(uid)
invoices = invoices_df(uid)
das_rows = list_das(uid)
docs = list_documents(uid)
employees = list_employees(uid)
contacts = list_contacts(uid)
obligations = list_obligations(uid)

with st.sidebar:
    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)
    st.caption("Ecossistema Razync • MEI")
    st.divider()
    page = st.radio(
        "Navegação",
        ["Dashboard","Movimentações","Relatório Mensal","Notas Fiscais","DAS","DASN-SIMEI",
         "Obrigações","Clientes e Fornecedores","Empregado","Documentos","Assistente Razync","Meu MEI","Backup"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(user["email"])
    if st.button("Sair", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()

year_revenue = float(transactions[(transactions["tx_type"]=="Receita") & (transactions["tx_date"].dt.year==CURRENT_YEAR)]["value"].sum()) if not transactions.empty else 0.0
year_expense = float(transactions[(transactions["tx_type"]=="Despesa") & (transactions["tx_date"].dt.year==CURRENT_YEAR)]["value"].sum()) if not transactions.empty else 0.0
limit = annual_limit(profile)
limit_pct = (year_revenue / limit * 100) if limit else 0

if page == "Dashboard":
    header("Visão geral", "Tudo que o seu MEI precisa acompanhar em um único painel.")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Receita no ano", brl(year_revenue))
    c2.metric("Despesas no ano", brl(year_expense))
    c3.metric("Resultado", brl(year_revenue-year_expense))
    c4.metric("Limite utilizado", f"{limit_pct:.1f}%")
    c5.metric("DAS pendentes", sum(1 for d in das_rows if d["status"]!="Pago"))

    left,right = st.columns([1.55,1])
    with left:
        st.subheader("Faturamento mensal")
        m = monthly_revenue_breakdown(transactions, CURRENT_YEAR)
        m["Mês"] = [calendar.month_abbr[int(x)] for x in m["month"]]
        fig = px.bar(m, x="Mês", y="receita")
        fig.update_layout(height=330, margin=dict(l=0,r=0,t=10,b=0), yaxis_title="Receita", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("O que precisa de atenção")
        if limit_pct >= 100:
            alert_box("⚠️ Faturamento atingiu ou ultrapassou o limite configurado. Procure orientação contábil para avaliar desenquadramento.", "danger")
        elif limit_pct >= 80:
            alert_box("⚠️ Você já utilizou mais de 80% do limite anual do MEI.", "warn")
        else:
            alert_box("✓ Faturamento dentro do limite monitorado.", "ok")
        pending_das = [d for d in das_rows if d["status"]!="Pago"]
        if pending_das:
            alert_box(f"⚠️ Existem {len(pending_das)} competência(s) de DAS pendente(s).", "warn")
        else:
            alert_box("✓ Nenhum DAS pendente registrado.", "ok")
        if not profile.get("cnpj"):
            alert_box("⚠️ Complete os dados em Meu MEI.", "warn")
        if date.today().month <= 5:
            alert_box("Lembrete: a DASN-SIMEI do ano anterior deve ser entregue até 31 de maio.", "warn")

    st.subheader("Últimos lançamentos")
    if transactions.empty:
        st.info("Nenhuma movimentação cadastrada.")
    else:
        show = transactions.head(10)[["tx_date","tx_type","description","category","value"]].copy()
        st.dataframe(show, use_container_width=True, hide_index=True,
                     column_config={"tx_date":st.column_config.DateColumn("Data",format="DD/MM/YYYY"),
                                    "value":st.column_config.NumberColumn("Valor",format="R$ %.2f")})

elif page == "Movimentações":
    header("Movimentações", "Registre receitas e despesas com informações suficientes para sua organização financeira.")
    with st.form("tx_form", clear_on_submit=True):
        a,b,c = st.columns(3)
        tx_type = a.selectbox("Tipo", ["Receita","Despesa"])
        tx_date = b.date_input("Data", date.today())
        value = c.number_input("Valor", min_value=0.0, step=10.0)
        desc = st.text_input("Descrição")
        d,e,f = st.columns(3)
        category = d.selectbox("Categoria", ["Vendas","Serviços","Fornecedores","Aluguel","Transporte","Marketing","Impostos","Folha","Outras"])
        counterparty = e.text_input("Cliente/fornecedor")
        payment_method = f.selectbox("Forma de pagamento", ["PIX","Dinheiro","Cartão","Boleto","Transferência","Outro"])
        document_number = st.text_input("Número do documento/nota (opcional)")
        if st.form_submit_button("Salvar lançamento", type="primary"):
            if value <= 0 or not desc.strip():
                st.error("Informe descrição e valor.")
            else:
                add_transaction(uid, tx_date=tx_date, tx_type=tx_type, description=desc.strip(), category=category,
                                value=float(value), document_number=document_number.strip(),
                                counterparty=counterparty.strip(), payment_method=payment_method)
                st.success("Lançamento salvo.")
                st.rerun()
    if not transactions.empty:
        st.dataframe(transactions[["id","tx_date","tx_type","description","category","counterparty","payment_method","value"]],
                     use_container_width=True, hide_index=True)
        with st.expander("Excluir lançamento"):
            item = st.selectbox("ID", transactions["id"].tolist())
            if st.button("Excluir definitivamente"):
                delete_transaction(uid, int(item)); st.rerun()

elif page == "Relatório Mensal":
    header("Relatório Mensal de Receitas Brutas", "Consolidação mensal para apoiar a obrigação do MEI e a DASN-SIMEI.")
    years = [CURRENT_YEAR]
    if not transactions.empty:
        years += [int(x) for x in transactions["tx_date"].dt.year.unique()]
    y = st.selectbox("Ano", sorted(set(years), reverse=True))
    mdf = monthly_revenue_breakdown(transactions, int(y))
    mdf["Mês"] = [calendar.month_name[int(x)] for x in mdf["month"]]
    mdf["Receita bruta"] = mdf["receita"]
    st.dataframe(mdf[["Mês","Receita bruta"]], use_container_width=True, hide_index=True,
                 column_config={"Receita bruta":st.column_config.NumberColumn(format="R$ %.2f")})
    st.metric("Total do ano", brl(float(mdf["receita"].sum())))
    st.info("O Relatório Mensal deve refletir a receita bruta do mês. Guarde também as notas e comprovantes relacionados.")
    csv = mdf[["Mês","Receita bruta"]].to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar relatório em CSV", csv, file_name=f"relatorio_mensal_{y}.csv", mime="text/csv")

elif page == "Notas Fiscais":
    header("Notas Fiscais", "Controle as notas emitidas e organize o faturamento documentado.")
    with st.form("invoice_form", clear_on_submit=True):
        a,b,c = st.columns(3)
        issue_date = a.date_input("Data de emissão", date.today())
        invoice_type = b.selectbox("Tipo", ["Serviço","Mercadoria"])
        number = c.text_input("Número")
        customer = st.text_input("Cliente")
        a,b = st.columns(2)
        customer_document = a.text_input("CPF/CNPJ do cliente")
        amount = b.number_input("Valor da nota", min_value=0.0)
        description = st.text_input("Descrição")
        status = st.selectbox("Situação", ["Emitida","Cancelada","Substituída"])
        if st.form_submit_button("Registrar nota", type="primary"):
            add_invoice(uid, issue_date=issue_date, invoice_type=invoice_type, number=number, customer=customer,
                        customer_document=customer_document, description=description, amount=float(amount), status=status)
            st.rerun()
    st.link_button("Abrir Emissor Nacional de NFS-e", "https://www.nfse.gov.br/EmissorNacional")
    if invoices.empty:
        st.info("Nenhuma nota registrada.")
    else:
        st.dataframe(invoices[["id","issue_date","invoice_type","number","customer","amount","status"]], use_container_width=True, hide_index=True)
        with st.expander("Excluir registro de nota"):
            iid = st.selectbox("ID da nota", invoices["id"].tolist())
            if st.button("Excluir nota do controle"):
                delete_invoice(uid, int(iid)); st.rerun()

elif page == "DAS":
    header("DAS", "Controle competência, vencimento, valor e pagamento da contribuição mensal.")
    with st.form("das_form"):
        a,b,c = st.columns(3)
        competence = a.text_input("Competência", value=date.today().strftime("%Y-%m"), help="Formato AAAA-MM")
        due = b.date_input("Vencimento", date.today())
        amount = c.number_input("Valor do DAS", min_value=0.0)
        status = st.selectbox("Status", ["Pendente","Pago","Atrasado"])
        payment_date = st.date_input("Data do pagamento", date.today()) if status=="Pago" else None
        notes = st.text_area("Observações")
        if st.form_submit_button("Salvar competência", type="primary"):
            upsert_das(uid, competence, due, float(amount), status, payment_date, notes)
            st.rerun()
    ddf = pd.DataFrame(list_das(uid))
    if ddf.empty:
        st.info("Nenhuma competência cadastrada.")
    else:
        st.dataframe(ddf, use_container_width=True, hide_index=True)
    st.info("O vencimento normal do DAS é no dia 20 de cada mês, passando ao dia útil seguinte quando aplicável.")

elif page == "DASN-SIMEI":
    header("DASN-SIMEI", "Prepare a declaração anual usando os dados registrados no Razync Pro.")
    selected_year = st.selectbox("Ano-calendário", list(range(CURRENT_YEAR-5, CURRENT_YEAR+1))[::-1])
    rev = float(transactions[(transactions["tx_type"]=="Receita") & (transactions["tx_date"].dt.year==selected_year)]["value"].sum()) if not transactions.empty else 0
    st.metric("Receita bruta anual apurada", brl(rev))
    st.metric("Empregado registrado no sistema", "Sim" if any(e["status"]=="Ativo" for e in employees) else "Não")
    st.info("Mesmo sem faturamento, a DASN-SIMEI deve ser apresentada. O envio oficial é feito no serviço da Receita/Simples Nacional.")
    summary = pd.DataFrame([{"ano":selected_year,"receita_bruta":rev,"teve_empregado":bool(employees)}])
    st.download_button("Baixar resumo para conferência", summary.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"dasn_resumo_{selected_year}.csv", mime="text/csv")

elif page == "Obrigações":
    header("Obrigações", "Agenda central de tarefas fiscais e administrativas do seu MEI.")
    with st.form("ob_form", clear_on_submit=True):
        a,b,c = st.columns(3)
        title = a.text_input("Obrigação/tarefa")
        due_date = b.date_input("Vencimento", date.today())
        category = c.selectbox("Categoria", ["Fiscal","Financeira","Trabalhista","Documental","Outra"])
        notes = st.text_input("Observações")
        if st.form_submit_button("Adicionar"):
            if title.strip():
                add_obligation(uid, title=title.strip(), due_date=due_date, category=category, notes=notes)
                st.rerun()
    odf = pd.DataFrame(list_obligations(uid))
    if odf.empty:
        st.info("Nenhuma obrigação adicional cadastrada.")
    else:
        st.dataframe(odf, use_container_width=True, hide_index=True)
        a,b = st.columns(2)
        with a:
            oid = st.selectbox("ID", odf["id"].tolist())
        with b:
            new_status = st.selectbox("Novo status", ["Pendente","Concluído"])
        if st.button("Atualizar status"):
            update_obligation_status(uid, int(oid), new_status); st.rerun()
        if st.button("Excluir obrigação"):
            delete_obligation(uid, int(oid)); st.rerun()

elif page == "Clientes e Fornecedores":
    header("Clientes e Fornecedores", "Cadastre contatos para organizar cobranças, vendas, compras e documentos.")
    with st.form("contact_form", clear_on_submit=True):
        a,b = st.columns(2)
        ctype = a.selectbox("Tipo", ["Cliente","Fornecedor"])
        name = b.text_input("Nome")
        a,b,c = st.columns(3)
        document = a.text_input("CPF/CNPJ")
        email = b.text_input("E-mail")
        phone = c.text_input("Telefone")
        notes = st.text_input("Observações")
        if st.form_submit_button("Salvar contato"):
            if name.strip():
                add_contact(uid, contact_type=ctype, name=name.strip(), document=document, email=email, phone=phone, notes=notes)
                st.rerun()
    cdf = pd.DataFrame(list_contacts(uid))
    if not cdf.empty:
        st.dataframe(cdf, use_container_width=True, hide_index=True)
        cid = st.selectbox("ID para excluir", cdf["id"].tolist())
        if st.button("Excluir contato"):
            delete_contact(uid, int(cid)); st.rerun()

elif page == "Empregado":
    header("Empregado", "Controle básico do empregado do MEI e mantenha a informação pronta para a declaração anual.")
    st.warning("O MEI deve observar os limites legais de contratação e remuneração vigentes. Use este módulo como controle administrativo.")
    with st.form("employee_form", clear_on_submit=True):
        a,b = st.columns(2)
        name = a.text_input("Nome do empregado")
        cpf = b.text_input("CPF")
        a,b,c = st.columns(3)
        admission = a.date_input("Admissão", date.today())
        salary = b.number_input("Salário", min_value=0.0)
        status = c.selectbox("Status", ["Ativo","Desligado"])
        notes = st.text_input("Observações")
        if st.form_submit_button("Salvar empregado"):
            if name.strip():
                add_employee(uid, name=name.strip(), cpf=cpf, admission_date=admission, salary=float(salary), status=status, notes=notes)
                st.rerun()
    edf = pd.DataFrame(list_employees(uid))
    if not edf.empty:
        st.dataframe(edf, use_container_width=True, hide_index=True)
        eid = st.selectbox("ID para excluir", edf["id"].tolist())
        if st.button("Excluir empregado"):
            delete_employee(uid, int(eid)); st.rerun()

elif page == "Documentos":
    header("Documentos", "Guarde notas, comprovantes, relatórios e documentos do MEI.")
    with st.form("doc_form", clear_on_submit=True):
        category = st.selectbox("Categoria", ["Nota fiscal","Comprovante DAS","Extrato","Relatório Mensal","Contrato","Documento do MEI","Outro"])
        reference_month = st.text_input("Competência/referência", placeholder="2026-08")
        file = st.file_uploader("Arquivo", type=["pdf","png","jpg","jpeg","xlsx","csv","xml","txt"])
        if st.form_submit_button("Salvar documento"):
            if file:
                save_document(uid, file.name, file.type or "", file.getvalue(), category, reference_month)
                st.success("Documento salvo."); st.rerun()
    ddf = pd.DataFrame(list_documents(uid))
    if not ddf.empty:
        st.dataframe(ddf, use_container_width=True, hide_index=True)
        did = st.selectbox("Documento", ddf["id"].tolist())
        doc = get_document(uid, int(did))
        if doc:
            st.download_button("Baixar documento", doc["content"], file_name=doc["filename"], mime=doc["mime_type"] or "application/octet-stream")
        if st.button("Excluir documento"):
            delete_document(uid, int(did)); st.rerun()

elif page == "Assistente Razync":
    header("Assistente Razync", "Faça perguntas sobre os dados do seu próprio MEI.")
    q = st.text_input("Pergunte algo", placeholder="Quanto faturei este ano? Tenho DAS pendente?")
    if q:
        low = q.lower()
        if "fatur" in low or "receita" in low:
            st.success(f"Seu faturamento registrado em {CURRENT_YEAR} é {brl(year_revenue)}. Isso representa {limit_pct:.1f}% do limite monitorado.")
        elif "despes" in low or "gasto" in low:
            st.success(f"Suas despesas registradas em {CURRENT_YEAR} somam {brl(year_expense)}.")
        elif "das" in low:
            pending = [d for d in das_rows if d["status"]!="Pago"]
            st.success(f"Você tem {len(pending)} competência(s) de DAS não marcadas como pagas.")
        elif "limite" in low:
            st.success(f"Limite monitorado: {brl(limit)}. Utilizado: {limit_pct:.1f}%.")
        else:
            st.info("No momento eu respondo sobre faturamento, despesas, DAS e limite. A integração com IA externa pode ampliar esse módulo.")

elif page == "Meu MEI":
    header("Meu MEI", "Dados cadastrais e parâmetros usados nos controles do Razync Pro.")
    opening_default = profile.get("opening_date") or date.today()
    if isinstance(opening_default, str):
        opening_default = date.fromisoformat(opening_default)
    activity_options = ["Serviços","Comércio","Indústria","Transporte"]
    current_activity = profile.get("activity_type") or "Serviços"
    activity_index = activity_options.index(current_activity) if current_activity in activity_options else 0
    with st.form("profile_form"):
        a,b = st.columns(2)
        business_name = a.text_input("Razão/Nome empresarial", value=profile.get("business_name") or "")
        trade_name = b.text_input("Nome fantasia", value=profile.get("trade_name") or "")
        a,b,c = st.columns(3)
        cnpj = a.text_input("CNPJ", value=profile.get("cnpj") or "")
        opening = b.date_input("Data de abertura", value=opening_default)
        activity_type = c.selectbox("Tipo principal", activity_options, index=activity_index)
        main_activity = st.text_input("Atividade principal", value=profile.get("main_activity") or "")
        a,b,c = st.columns(3)
        city = a.text_input("Cidade", value=profile.get("city") or "")
        state = b.text_input("UF", value=profile.get("state") or "", max_chars=2)
        phone = c.text_input("Telefone", value=profile.get("phone") or "")
        a,b = st.columns(2)
        municipal_registration = a.text_input("Inscrição municipal", value=profile.get("municipal_registration") or "")
        state_registration = b.text_input("Inscrição estadual", value=profile.get("state_registration") or "")
        configured_limit = st.number_input("Limite anual configurado", min_value=0.0, value=float(profile.get("annual_limit") or MEI_ANNUAL_LIMIT_2026))
        if st.form_submit_button("Salvar dados", type="primary"):
            save_profile(uid, business_name=business_name, trade_name=trade_name, cnpj=cnpj, opening_date=opening,
                         activity_type=activity_type, main_activity=main_activity, city=city, state=state.upper(),
                         phone=phone, municipal_registration=municipal_registration, state_registration=state_registration,
                         annual_limit=float(configured_limit))
            st.success("Dados salvos."); st.rerun()
    st.caption(f"Limite efetivamente monitorado para {CURRENT_YEAR}: {brl(annual_limit(get_profile(uid)))}")

elif page == "Backup":
    header("Backup e exportação", "Exporte seus dados para conferência, arquivo pessoal ou migração.")
    buffers = {}
    buffers["movimentacoes.csv"] = transactions.to_csv(index=False).encode("utf-8-sig")
    buffers["notas.csv"] = invoices.to_csv(index=False).encode("utf-8-sig") if not invoices.empty else b""
    buffers["das.csv"] = pd.DataFrame(das_rows).to_csv(index=False).encode("utf-8-sig")
    buffers["contatos.csv"] = pd.DataFrame(contacts).to_csv(index=False).encode("utf-8-sig")
    buffers["empregados.csv"] = pd.DataFrame(employees).to_csv(index=False).encode("utf-8-sig")
    for name, content in buffers.items():
        st.download_button(f"Baixar {name}", content, file_name=name, mime="text/csv")

st.divider()
st.caption("Razync Pro • Ecossistema Razync • gestão e organização para MEI")
