from __future__ import annotations

from datetime import date, datetime
import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    add_transaction, authenticate, create_user, delete_document, delete_transaction,
    get_document, get_profile, init_db, list_das, list_documents,
    list_transactions, save_document, save_profile, upsert_das,
)

st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
:root { --rz-blue:#2563eb; --rz-dark:#050914; --rz-card:#0b1220; --rz-border:#1f2a3d; }
.stApp { background:radial-gradient(circle at 15% 0%, #0b1832 0%, #050914 34%, #050914 100%); }
[data-testid="stSidebar"] { background:#070c16; border-right:1px solid #172236; }
[data-testid="stMetric"] { background:linear-gradient(180deg,rgba(17,28,49,.95),rgba(9,16,29,.95)); border:1px solid #1d2a42; border-radius:16px; padding:14px 16px; }
.block-container { padding-top:1.25rem; padding-bottom:2rem; max-width:1450px; }
.rz-brand { font-size:1.48rem; font-weight:900; letter-spacing:-.03em; }
.rz-brand span { color:#60a5fa; }
.rz-kicker { color:#60a5fa; font-weight:800; text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; }
.rz-title { font-size:2rem; font-weight:900; margin:.15rem 0 .2rem; letter-spacing:-.035em; }
.rz-sub { color:#94a3b8; margin-bottom:1.2rem; }
.rz-card { background:rgba(10,18,32,.86); border:1px solid #1c2940; border-radius:16px; padding:16px; }
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
    st.markdown('<div class="rz-kicker">Razync Pro</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-sub">{subtitle}</div>', unsafe_allow_html=True)


def tx_dataframe(user_id: int) -> pd.DataFrame:
    df = pd.DataFrame(list_transactions(user_id))
    if df.empty:
        return pd.DataFrame(columns=["id", "tx_date", "tx_type", "description", "category", "value"])
    df["tx_date"] = pd.to_datetime(df["tx_date"])
    return df


def ensure_login() -> dict:
    if "user" in st.session_state:
        return st.session_state.user
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)
        st.caption("Gestão inteligente para MEI e pequenos negócios")
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
                    else:
                        st.error("E-mail ou senha inválidos.")
        with register_tab:
            with st.form("register_form"):
                name = st.text_input("Seu nome")
                email = st.text_input("E-mail", key="reg_email")
                password = st.text_input("Senha", type="password", key="reg_password")
                confirm = st.text_input("Confirmar senha", type="password")
                if st.form_submit_button("Criar conta", use_container_width=True):
                    if len(name.strip()) < 2: st.error("Informe seu nome.")
                    elif "@" not in email: st.error("Informe um e-mail válido.")
                    elif len(password) < 6: st.error("Use uma senha com pelo menos 6 caracteres.")
                    elif password != confirm: st.error("As senhas não conferem.")
                    else:
                        ok, message = create_user(name, email, password)
                        st.success(message + " Agora faça login.") if ok else st.error(message)
    st.stop()


user = ensure_login()
user_id = int(user["id"])
profile = get_profile(user_id)
transactions = tx_dataframe(user_id)
total_receitas = float(transactions.loc[transactions["tx_type"] == "Receita", "value"].sum()) if not transactions.empty else 0.0
total_despesas = float(transactions.loc[transactions["tx_type"] == "Despesa", "value"].sum()) if not transactions.empty else 0.0
resultado = total_receitas - total_despesas
annual_limit = float(profile.get("annual_limit") or 0)
usage_pct = (total_receitas / annual_limit * 100) if annual_limit > 0 else 0

with st.sidebar:
    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)
    st.caption("Ecossistema Razync • MEI")
    st.divider()
    page = st.radio("Navegação", ["Dashboard", "Receitas", "Despesas", "Fluxo de caixa", "DAS", "Declaração anual", "Documentos", "Assistente", "Meu MEI"], label_visibility="collapsed")
    st.divider()
    st.caption(user.get("email", ""))
    if st.button("Sair", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()

if page == "Dashboard":
    header("Visão geral", f"Olá, {user.get('name', '').split(' ')[0]}. Veja o que precisa da sua atenção.")
    a, b, c, d = st.columns(4)
    a.metric("Faturamento registrado", brl(total_receitas)); b.metric("Despesas registradas", brl(total_despesas)); c.metric("Resultado estimado", brl(resultado)); d.metric("Uso do limite informado", f"{usage_pct:.1f}%" if annual_limit > 0 else "Não definido")
    st.divider()
    left, right = st.columns([1.65, 1])
    with left:
        st.subheader("Movimentação")
        if transactions.empty: st.info("Cadastre sua primeira receita ou despesa.")
        else:
            monthly = transactions.copy(); monthly["mes"] = monthly["tx_date"].dt.to_period("M").astype(str)
            chart = monthly.groupby(["mes", "tx_type"], as_index=False)["value"].sum()
            fig = px.bar(chart, x="mes", y="value", color="tx_type", barmode="group")
            fig.update_layout(height=330, margin=dict(l=0,r=0,t=8,b=0), legend_title_text="", xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("O que preciso fazer agora?")
        alerts = []; das_df = pd.DataFrame(list_das(user_id)); today = pd.Timestamp(date.today())
        if not profile.get("cnpj"): alerts.append(("warn", "Complete os dados do MEI", "Cadastre CNPJ, atividade e data de abertura."))
        if annual_limit <= 0: alerts.append(("warn", "Defina seu limite anual", "Informe o limite aplicável ao seu caso em Meu MEI."))
        elif usage_pct >= 90: alerts.append(("danger", "Atenção ao faturamento", f"Você registrou {usage_pct:.1f}% do limite informado."))
        elif usage_pct >= 70: alerts.append(("warn", "Faturamento em acompanhamento", f"Você registrou {usage_pct:.1f}% do limite informado."))
        if not das_df.empty:
            das_df["due_date"] = pd.to_datetime(das_df["due_date"], errors="coerce")
            overdue = das_df[(das_df["status"] != "Pago") & das_df["due_date"].notna() & (das_df["due_date"] < today)]
            if not overdue.empty: alerts.append(("danger", "Há DAS marcado como atrasado", f"{len(overdue)} competência(s) precisam de revisão."))
        if not alerts: alerts.append(("ok", "Tudo organizado por aqui", "Continue registrando as movimentações e obrigações."))
        for kind, title, text in alerts:
            st.markdown(f'<div class="rz-alert rz-{kind}"><b>{title}</b><div class="rz-small">{text}</div></div>', unsafe_allow_html=True)
    st.subheader("Últimos lançamentos")
    if transactions.empty: st.caption("Nenhum lançamento cadastrado.")
    else:
        st.dataframe(transactions.head(8)[["tx_date","tx_type","description","category","value"]], use_container_width=True, hide_index=True, column_config={"tx_date":st.column_config.DateColumn("Data",format="DD/MM/YYYY"),"tx_type":"Tipo","description":"Descrição","category":"Categoria","value":st.column_config.NumberColumn("Valor",format="R$ %.2f")})

elif page in ("Receitas", "Despesas"):
    tx_type = "Receita" if page == "Receitas" else "Despesa"; header(page, f"Cadastre e acompanhe suas {page.lower()}.")
    categories = ["Vendas","Serviços","Marketplace","Outras receitas"] if tx_type == "Receita" else ["Fornecedores","Serviços","Aluguel","Transporte","Marketing","Impostos","Outras despesas"]
    with st.form(f"form_{tx_type.lower()}", clear_on_submit=True):
        c1,c2=st.columns(2); tx_date=c1.date_input("Data",value=date.today(),key=f"date_{tx_type}"); value=c2.number_input("Valor",min_value=0.0,step=10.0,format="%.2f",key=f"value_{tx_type}")
        description=st.text_input("Descrição",placeholder="Ex.: venda, cliente, fornecedor, conta..."); category=st.selectbox("Categoria",categories)
        if st.form_submit_button(f"Adicionar {tx_type.lower()}",type="primary",use_container_width=True):
            if value <= 0 or not description.strip(): st.error("Informe uma descrição e um valor maior que zero.")
            else: add_transaction(user_id,tx_date.isoformat(),tx_type,description.strip(),category,float(value)); st.success(f"{tx_type} adicionada."); st.rerun()
    subset=transactions[transactions["tx_type"]==tx_type] if not transactions.empty else transactions
    st.metric(f"Total de {page.lower()}",brl(float(subset["value"].sum()) if not subset.empty else 0.0))
    if subset.empty: st.info(f"Nenhuma {tx_type.lower()} cadastrada.")
    else:
        st.dataframe(subset[["tx_date","description","category","value"]],use_container_width=True,hide_index=True,column_config={"tx_date":st.column_config.DateColumn("Data",format="DD/MM/YYYY"),"description":"Descrição","category":"Categoria","value":st.column_config.NumberColumn("Valor",format="R$ %.2f")})
        ids={f"#{int(r.id)} • {r.description} • {brl(float(r.value))}":int(r.id) for r in subset.itertuples()}; selected=st.selectbox("Excluir lançamento",["Selecione..."]+list(ids.keys()))
        if selected!="Selecione..." and st.button("Excluir selecionado"): delete_transaction(user_id,ids[selected]); st.rerun()

elif page == "Fluxo de caixa":
    header("Fluxo de caixa","Acompanhe entradas, saídas e evolução do saldo.")
    a,b,c=st.columns(3); a.metric("Entradas",brl(total_receitas)); b.metric("Saídas",brl(total_despesas)); c.metric("Saldo",brl(resultado))
    if transactions.empty: st.info("Cadastre movimentações para visualizar o fluxo.")
    else:
        flow=transactions.sort_values(["tx_date","id"]).copy(); flow["impact"]=flow.apply(lambda r:r["value"] if r["tx_type"]=="Receita" else -r["value"],axis=1); flow["saldo"]=flow["impact"].cumsum()
        fig=px.line(flow,x="tx_date",y="saldo",markers=True); fig.update_layout(height=340,margin=dict(l=0,r=0,t=8,b=0),xaxis_title="",yaxis_title=""); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(flow[["tx_date","tx_type","description","category","value","saldo"]].sort_values("tx_date",ascending=False),use_container_width=True,hide_index=True)
        st.download_button("Baixar fluxo de caixa em CSV",flow.to_csv(index=False).encode("utf-8-sig"),"razync_pro_fluxo_caixa.csv","text/csv")

elif page == "DAS":
    header("DAS","Controle mensal das competências e pagamentos.")
    current_year=date.today().year; months=[f"{current_year}-{m:02d}" for m in range(1,13)]
    with st.form("das_form"):
        competence=st.selectbox("Competência",months); year,month=map(int,competence.split("-")); default_due=date(year,month,min(20,calendar.monthrange(year,month)[1])); c1,c2=st.columns(2)
        due_date=c1.date_input("Vencimento",value=default_due); amount=c2.number_input("Valor do DAS",min_value=0.0,format="%.2f"); status=st.selectbox("Situação",["Pendente","Pago","Atrasado"]); payment_date=st.date_input("Data do pagamento",value=date.today()) if status=="Pago" else None; notes=st.text_input("Observações")
        if st.form_submit_button("Salvar competência",type="primary",use_container_width=True): upsert_das(user_id,competence,due_date.isoformat(),float(amount),status,payment_date.isoformat() if payment_date else None,notes); st.success("DAS atualizado."); st.rerun()
    das_df=pd.DataFrame(list_das(user_id))
    if das_df.empty: st.info("Nenhuma competência cadastrada.")
    else:
        das_df["due_date"]=pd.to_datetime(das_df["due_date"],errors="coerce"); auto_late=(das_df["status"]!="Pago") & das_df["due_date"].notna() & (das_df["due_date"]<pd.Timestamp(date.today())); das_df.loc[auto_late,"status"]="Atrasado"
        st.dataframe(das_df[["competence","due_date","amount","status","payment_date","notes"]],use_container_width=True,hide_index=True,column_config={"competence":"Competência","due_date":st.column_config.DateColumn("Vencimento",format="DD/MM/YYYY"),"amount":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"status":"Situação","payment_date":"Pagamento","notes":"Observações"})

elif page == "Declaração anual":
    header("Declaração anual","Consolide o que foi registrado ao longo do ano.")
    if transactions.empty: st.info("Cadastre receitas para gerar o resumo anual.")
    else:
        years=sorted(transactions["tx_date"].dt.year.unique().tolist(),reverse=True); selected_year=st.selectbox("Ano",years); yr=transactions[transactions["tx_date"].dt.year==selected_year]; revenue=float(yr.loc[yr["tx_type"]=="Receita","value"].sum()); expense=float(yr.loc[yr["tx_type"]=="Despesa","value"].sum())
        a,b,c=st.columns(3); a.metric("Receitas do ano",brl(revenue)); b.metric("Despesas do ano",brl(expense)); c.metric("Resultado estimado",brl(revenue-expense))
        revenue_by_category=yr[yr["tx_type"]=="Receita"].groupby("category",as_index=False)["value"].sum()
        if not revenue_by_category.empty: st.subheader("Receitas por categoria"); st.dataframe(revenue_by_category,use_container_width=True,hide_index=True)
        st.caption("Este resumo organiza os dados cadastrados no Razync Pro; ele não substitui validação fiscal nem envio oficial da declaração.")

elif page == "Documentos":
    header("Documentos","Guarde comprovantes, notas, extratos e arquivos do negócio.")
    with st.form("document_form",clear_on_submit=True):
        category=st.selectbox("Categoria",["Nota fiscal","Comprovante","Extrato","Contrato","DAS","Outros"]); upload=st.file_uploader("Arquivo",type=["pdf","png","jpg","jpeg","xlsx","csv"])
        if st.form_submit_button("Salvar documento",type="primary",use_container_width=True):
            if upload is None: st.error("Selecione um arquivo.")
            else: save_document(user_id,upload.name,upload.type or "",upload.getvalue(),category); st.success("Documento salvo."); st.rerun()
    docs=list_documents(user_id)
    if not docs: st.info("Nenhum documento salvo.")
    else:
        for doc in docs:
            with st.expander(f"{doc['category']} • {doc['filename']}"):
                st.caption(f"{doc['size_bytes']/1024:.1f} KB • {doc['created_at']}"); full=get_document(user_id,int(doc["id"]))
                if full: st.download_button("Baixar",full["content"],file_name=full["filename"],mime=full["mime_type"] or "application/octet-stream",key=f"download_{doc['id']}")
                if st.button("Excluir",key=f"delete_doc_{doc['id']}"): delete_document(user_id,int(doc["id"])); st.rerun()

elif page == "Assistente":
    header("Assistente Razync","Pergunte sobre os dados que você registrou no sistema.")
    st.caption("Nesta etapa o assistente analisa os dados locais. Uma integração com IA externa pode ser adicionada depois.")
    question=st.text_input("Pergunte algo",placeholder="Ex.: quanto faturei? quanto gastei? como está meu saldo?")
    if question:
        q=question.lower()
        if any(k in q for k in ["faturei","faturamento","receita","entrou"]): answer=f"Você registrou {brl(total_receitas)} em receitas."
        elif any(k in q for k in ["gastei","despesa","gasto","saiu"]): answer=f"Você registrou {brl(total_despesas)} em despesas."
        elif any(k in q for k in ["saldo","resultado","lucro","sobrou"]): answer=f"Seu resultado estimado, considerando os lançamentos registrados, é {brl(resultado)}."
        elif any(k in q for k in ["limite","quanto posso faturar"]): answer=f"Com base no limite que você informou no cadastro, ainda restam {brl(max(annual_limit-total_receitas,0))}. Uso atual: {usage_pct:.1f}%." if annual_limit>0 else "Você ainda não informou um limite anual em Meu MEI."
        elif "das" in q:
            das_df=pd.DataFrame(list_das(user_id)); answer="Você ainda não cadastrou competências do DAS." if das_df.empty else f"Você tem {int((das_df['status']!='Pago').sum())} competência(s) do DAS sem status de pago."
        else: answer="Consigo responder sobre faturamento, despesas, saldo, limite informado e DAS."
        st.markdown(f'<div class="rz-card"><b>Razync</b><br>{answer}</div>',unsafe_allow_html=True)

elif page == "Meu MEI":
    header("Meu MEI","Dados principais e parâmetros do seu negócio.")
    opening=profile.get("opening_date")
    try: opening_value=datetime.strptime(opening,"%Y-%m-%d").date() if opening else date.today()
    except ValueError: opening_value=date.today()
    with st.form("profile_form"):
        business_name=st.text_input("Nome do negócio",value=profile.get("business_name") or ""); cnpj=st.text_input("CNPJ",value=profile.get("cnpj") or "",placeholder="00.000.000/0000-00"); main_activity=st.text_input("Atividade principal",value=profile.get("main_activity") or ""); c1,c2=st.columns(2); opening_date=c1.date_input("Data de abertura",value=opening_value); annual_limit_input=c2.number_input("Limite anual aplicável ao seu caso",min_value=0.0,value=float(profile.get("annual_limit") or 0),step=1000.0,format="%.2f"); c3,c4=st.columns(2); phone=c3.text_input("Telefone",value=profile.get("phone") or ""); city=c4.text_input("Cidade",value=profile.get("city") or "")
        st.caption("O limite fica configurável para evitar que o sistema dependa de um valor fiscal fixo no código.")
        if st.form_submit_button("Salvar dados",type="primary",use_container_width=True): save_profile(user_id,business_name,cnpj,main_activity,opening_date.isoformat(),float(annual_limit_input),phone,city); st.success("Dados atualizados."); st.rerun()

st.divider(); st.caption("Razync Pro • Ecossistema Razync • versão MVP")
