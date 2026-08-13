from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    add_lancamento,
    delete_lancamento,
    get_fluxo_mensal,
    get_lancamentos,
    get_mei,
    get_resumo,
    init_db,
    save_mei,
)

st.set_page_config(
    page_title="MEI Fácil",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1450px;}
      [data-testid="stSidebar"] {background: linear-gradient(180deg,#07111f 0%,#0b1728 100%); border-right: 1px solid #1b2a40;}
      [data-testid="stSidebar"] * {color: #eaf2ff;}
      .hero {padding: 1.25rem 1.35rem; border-radius: 22px; background: linear-gradient(135deg,#07111f 0%,#10233f 58%,#0c4664 100%); border:1px solid #1d3954; margin-bottom: 1.2rem;}
      .hero h1 {font-size: 2rem; margin:0; color:#fff;}
      .hero p {margin:.35rem 0 0; color:#a9bdd5;}
      .eyebrow {font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:#5ad5ff; font-weight:700; margin-bottom:.35rem;}
      .section-title {font-size:1.15rem; font-weight:750; margin:1.1rem 0 .7rem;}
      .notice {padding: .9rem 1rem; border-radius: 16px; border: 1px solid rgba(125,145,170,.2); margin-bottom:.65rem; background:rgba(255,255,255,.02);}
      .notice.good {border-left:4px solid #28c281;}
      .notice.warn {border-left:4px solid #ffb44a;}
      .notice.info {border-left:4px solid #4aa8ff;}
      .muted {opacity:.66; font-size:.9rem;}
      div[data-testid="stMetric"] {border:1px solid rgba(125,145,170,.18); padding:1rem; border-radius:18px; background:rgba(125,145,170,.035);}
      div[data-testid="stMetricValue"] {font-size:1.55rem;}
      .small-card {border:1px solid rgba(125,145,170,.18); border-radius:18px; padding:1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def hero(title: str, subtitle: str, eyebrow: str = "MEI FÁCIL") -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dataframe_lancamentos(df: pd.DataFrame, key: str) -> None:
    if df.empty:
        st.info("Nenhum lançamento cadastrado ainda.")
        return

    show = df.copy()
    st.dataframe(
        show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "tipo": "Tipo",
            "descricao": "Descrição",
            "categoria": "Categoria",
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
        },
        key=key,
    )


def delete_box(df: pd.DataFrame, key: str) -> None:
    if df.empty:
        return
    ids = df["id"].astype(int).tolist()
    with st.expander("Excluir lançamento"):
        selected = st.selectbox("Selecione o ID", ids, key=f"delete_{key}")
        row = df[df["id"] == selected].iloc[0]
        st.caption(f"{row['descricao']} • {brl(float(row['valor']))}")
        if st.button("Excluir definitivamente", key=f"btn_{key}", type="secondary"):
            delete_lancamento(selected)
            st.success("Lançamento excluído.")
            st.rerun()


with st.sidebar:
    st.markdown("## 🧾 MEI Fácil")
    st.caption("Organização financeira sem complicação")
    st.divider()
    pagina = st.radio(
        "Navegação",
        [
            "Dashboard",
            "Receitas",
            "Despesas",
            "Fluxo de caixa",
            "DAS",
            "Declaração anual",
            "Documentos",
            "Meu MEI",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("MVP v0.2 • Streamlit + SQLite")

resumo = get_resumo()
receitas = get_lancamentos("Receita")
despesas = get_lancamentos("Despesa")
todos = get_lancamentos()
mei = get_mei()

if pagina == "Dashboard":
    nome = str(mei.get("nome") or "seu negócio")
    hero("Visão geral", f"Acompanhe as principais informações de {nome} em um só lugar.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento", brl(resumo["receitas"]))
    c2.metric("Despesas", brl(resumo["despesas"]))
    c3.metric("Resultado estimado", brl(resumo["resultado"]))
    c4.metric("Lançamentos", int(resumo["quantidade"]))

    st.markdown('<div class="section-title">Evolução financeira</div>', unsafe_allow_html=True)
    fluxo_mensal = get_fluxo_mensal()
    left, right = st.columns([1.55, 1])

    with left:
        if fluxo_mensal.empty:
            st.info("Cadastre receitas e despesas para começar a visualizar a evolução mensal.")
        else:
            chart = fluxo_mensal.melt(
                id_vars=["mes"],
                value_vars=["receitas", "despesas"],
                var_name="tipo",
                value_name="valor",
            )
            fig = px.bar(chart, x="mes", y="valor", color="tipo", barmode="group")
            fig.update_layout(
                height=355,
                margin=dict(l=0, r=0, t=15, b=0),
                legend_title_text="",
                xaxis_title="",
                yaxis_title="R$",
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### O que preciso fazer agora?")
        if not mei.get("cnpj"):
            st.markdown('<div class="notice warn"><b>⚠ Complete os dados do seu MEI</b><br><span class="muted">Cadastre CNPJ, atividade e data de abertura em Meu MEI.</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="notice good"><b>✓ Cadastro do MEI preenchido</b><br><span class="muted">Os dados principais do negócio estão salvos.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="notice info"><b>ℹ Registre as movimentações</b><br><span class="muted">Quanto mais completo o histórico, melhores serão os relatórios.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="notice warn"><b>⚠ Módulo DAS em construção</b><br><span class="muted">O controle de vencimentos e pagamentos será a próxima etapa.</span></div>', unsafe_allow_html=True)

    if float(mei.get("limite_anual") or 0) > 0:
        limite = float(mei["limite_anual"])
        usado = min(resumo["receitas"] / limite, 1.0) if limite else 0.0
        st.markdown('<div class="section-title">Acompanhamento do limite configurado</div>', unsafe_allow_html=True)
        st.progress(usado)
        st.caption(f"{brl(resumo['receitas'])} registrados de {brl(limite)} configurados para o ano.")

    st.markdown('<div class="section-title">Últimos lançamentos</div>', unsafe_allow_html=True)
    dataframe_lancamentos(todos.head(10), "dashboard_table")

elif pagina == "Receitas":
    hero("Receitas", "Registre vendas, serviços e outras entradas do seu negócio.", "FINANCEIRO")
    with st.form("nova_receita", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data_receita = c1.date_input("Data", value=date.today())
        valor_receita = c2.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
        descricao_receita = st.text_input("Descrição", placeholder="Ex.: serviço realizado para cliente")
        categoria_receita = st.selectbox("Categoria", ["Vendas", "Serviços", "Outras receitas"])
        salvar = st.form_submit_button("Adicionar receita", type="primary", use_container_width=True)
        if salvar:
            if not descricao_receita.strip() or valor_receita <= 0:
                st.error("Informe uma descrição e um valor maior que zero.")
            else:
                add_lancamento(data_receita.isoformat(), "Receita", descricao_receita, categoria_receita, valor_receita)
                st.success("Receita salva no banco.")
                st.rerun()

    c1, c2 = st.columns([1, 3])
    c1.metric("Total registrado", brl(resumo["receitas"]))
    c2.caption("Os lançamentos ficam salvos no banco SQLite local deste ambiente.")
    dataframe_lancamentos(receitas, "receitas_table")
    delete_box(receitas, "receita")

elif pagina == "Despesas":
    hero("Despesas", "Organize os gastos para entender melhor para onde o dinheiro está indo.", "FINANCEIRO")
    with st.form("nova_despesa", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data_despesa = c1.date_input("Data", value=date.today(), key="despesa_data")
        valor_despesa = c2.number_input("Valor", min_value=0.0, step=10.0, format="%.2f", key="despesa_valor")
        descricao_despesa = st.text_input("Descrição", placeholder="Ex.: fornecedor, internet ou combustível")
        categoria_despesa = st.selectbox("Categoria", ["Fornecedores", "Serviços", "Aluguel", "Transporte", "Marketing", "Impostos", "Outras despesas"])
        salvar = st.form_submit_button("Adicionar despesa", type="primary", use_container_width=True)
        if salvar:
            if not descricao_despesa.strip() or valor_despesa <= 0:
                st.error("Informe uma descrição e um valor maior que zero.")
            else:
                add_lancamento(data_despesa.isoformat(), "Despesa", descricao_despesa, categoria_despesa, valor_despesa)
                st.success("Despesa salva no banco.")
                st.rerun()

    st.metric("Total registrado", brl(resumo["despesas"]))
    dataframe_lancamentos(despesas, "despesas_table")
    delete_box(despesas, "despesa")

elif pagina == "Fluxo de caixa":
    hero("Fluxo de caixa", "Visualize entradas, saídas e saldo acumulado ao longo do tempo.", "FINANCEIRO")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", brl(resumo["receitas"]))
    c2.metric("Saídas", brl(resumo["despesas"]))
    c3.metric("Saldo", brl(resumo["resultado"]))

    if todos.empty:
        st.info("Cadastre movimentações para visualizar o fluxo de caixa.")
    else:
        fluxo = todos.sort_values(["data", "id"]).copy()
        fluxo["movimento"] = fluxo.apply(lambda r: float(r["valor"]) if r["tipo"] == "Receita" else -float(r["valor"]), axis=1)
        fluxo["saldo_acumulado"] = fluxo["movimento"].cumsum()
        fig = px.line(fluxo, x="data", y="saldo_acumulado", markers=True)
        fig.update_layout(height=370, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="Saldo")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            fluxo[["data", "tipo", "descricao", "categoria", "movimento", "saldo_acumulado"]].sort_values("data", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "movimento": st.column_config.NumberColumn("Movimento", format="R$ %.2f"),
                "saldo_acumulado": st.column_config.NumberColumn("Saldo acumulado", format="R$ %.2f"),
            },
        )

elif pagina == "DAS":
    hero("DAS", "Central de acompanhamento das obrigações mensais do MEI.", "OBRIGAÇÕES")
    st.info("Nesta etapa ainda não estamos calculando nem emitindo DAS. Vamos criar primeiro o controle de competências, vencimentos, pagamentos e comprovantes.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Pendentes", "—")
    col2.metric("Pagos", "—")
    col3.metric("Atrasados", "—")
    st.markdown("#### Próxima implementação")
    st.write("Calendário mensal, status do DAS, data de pagamento, comprovante e alertas no Dashboard.")

elif pagina == "Declaração anual":
    hero("Declaração anual", "Organize os dados que serão usados na preparação da DASN-SIMEI.", "OBRIGAÇÕES")
    ano_atual = datetime.now().year
    st.metric(f"Faturamento registrado em {ano_atual}", brl(resumo["receitas"]))
    st.warning("Este módulo é organizacional nesta fase. O envio oficial da declaração ainda não é realizado pelo sistema.")
    if receitas.empty:
        st.info("Ainda não existem receitas para consolidar.")
    else:
        consolidado = receitas.copy()
        consolidado["ano"] = consolidado["data"].dt.year
        consolidado = consolidado.groupby("ano", as_index=False)["valor"].sum()
        st.dataframe(consolidado, hide_index=True, use_container_width=True, column_config={"valor": st.column_config.NumberColumn("Faturamento", format="R$ %.2f")})

elif pagina == "Documentos":
    hero("Documentos", "Separe comprovantes, notas e arquivos importantes do seu negócio.", "ARQUIVOS")
    arquivo = st.file_uploader("Selecionar documento", type=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"])
    if arquivo is not None:
        st.success(f"Arquivo selecionado: {arquivo.name}")
        st.caption("O armazenamento permanente será adicionado quando conectarmos um serviço externo de arquivos.")

elif pagina == "Meu MEI":
    hero("Meu MEI", "Cadastre os dados principais do negócio e personalize o acompanhamento.", "CADASTRO")

    data_salva = mei.get("data_abertura")
    try:
        abertura_default = date.fromisoformat(str(data_salva)) if data_salva else date.today()
    except ValueError:
        abertura_default = date.today()

    with st.form("dados_mei"):
        nome = st.text_input("Nome do negócio", value=str(mei.get("nome") or ""))
        cnpj = st.text_input("CNPJ", value=str(mei.get("cnpj") or ""), placeholder="00.000.000/0000-00")
        atividade = st.text_input("Atividade principal", value=str(mei.get("atividade") or ""))
        c1, c2 = st.columns(2)
        abertura = c1.date_input("Data de abertura", value=abertura_default)
        limite = c2.number_input("Limite anual para acompanhamento", min_value=0.0, value=float(mei.get("limite_anual") or 0), step=1000.0, format="%.2f", help="Campo configurável. Use o limite que se aplica ao seu caso e ao ano acompanhado.")
        enviado = st.form_submit_button("Salvar dados", type="primary", use_container_width=True)
        if enviado:
            save_mei(nome, cnpj, atividade, abertura.isoformat(), limite)
            st.success("Dados do MEI salvos.")
            st.rerun()

    st.caption("O limite anual é configurável de propósito para evitar deixar regras fiscais fixas no código.")

st.divider()
st.caption("MEI Fácil • MVP v0.2 • Streamlit + SQLite")
