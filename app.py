from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="MEI Fácil",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Estado inicial da aplicação
# -----------------------------
if "receitas" not in st.session_state:
    st.session_state.receitas = [
        {"data": date.today(), "descricao": "Venda demonstrativa", "categoria": "Vendas", "valor": 1800.00}
    ]

if "despesas" not in st.session_state:
    st.session_state.despesas = [
        {"data": date.today(), "descricao": "Internet", "categoria": "Serviços", "valor": 149.90}
    ]


# -----------------------------
# Estilo
# -----------------------------
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        [data-testid="stSidebar"] {border-right: 1px solid rgba(120,120,120,.18);}
        .mei-title {font-size: 2rem; font-weight: 800; margin-bottom: .15rem;}
        .mei-subtitle {opacity: .7; margin-bottom: 1.4rem;}
        .status-box {
            border: 1px solid rgba(120,120,120,.2);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: .75rem;
        }
        .status-good {border-left: 5px solid #2fb170;}
        .status-warn {border-left: 5px solid #f0a33a;}
        .helper {font-size: .9rem; opacity: .7;}
    </style>
    """,
    unsafe_allow_html=True,
)


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def receitas_df() -> pd.DataFrame:
    df = pd.DataFrame(st.session_state.receitas)
    if df.empty:
        return pd.DataFrame(columns=["data", "descricao", "categoria", "valor"])
    df["data"] = pd.to_datetime(df["data"])
    return df


def despesas_df() -> pd.DataFrame:
    df = pd.DataFrame(st.session_state.despesas)
    if df.empty:
        return pd.DataFrame(columns=["data", "descricao", "categoria", "valor"])
    df["data"] = pd.to_datetime(df["data"])
    return df


def header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="mei-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mei-subtitle">{subtitle}</div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## 🧾 MEI Fácil")
    st.caption("Sua rotina financeira em um só lugar")
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
    st.caption("MVP • dados salvos apenas durante esta sessão")


receitas = receitas_df()
despesas = despesas_df()
total_receitas = float(receitas["valor"].sum()) if not receitas.empty else 0.0
total_despesas = float(despesas["valor"].sum()) if not despesas.empty else 0.0
resultado = total_receitas - total_despesas


if pagina == "Dashboard":
    header("Visão geral", "Veja como está o seu MEI hoje.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento", brl(total_receitas))
    c2.metric("Despesas", brl(total_despesas))
    c3.metric("Resultado estimado", brl(resultado))
    c4.metric("Lançamentos", len(receitas) + len(despesas))

    st.divider()
    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Entradas x saídas")
        chart_df = pd.DataFrame(
            {
                "Tipo": ["Receitas", "Despesas"],
                "Valor": [total_receitas, total_despesas],
            }
        )
        fig = px.bar(chart_df, x="Tipo", y="Valor", text_auto=".2s")
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=340)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("O que preciso fazer agora?")
        st.markdown(
            '<div class="status-box status-good"><b>✓ Organização financeira ativa</b><br><span class="helper">Continue registrando receitas e despesas.</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="status-box status-warn"><b>⚠ DAS ainda não está conectado</b><br><span class="helper">Na próxima etapa vamos criar calendário e controle de pagamentos.</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="status-box status-warn"><b>⚠ Dados ainda são temporários</b><br><span class="helper">Vamos adicionar banco de dados e login nas próximas versões.</span></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Últimos lançamentos")
    movimentos = []
    for item in st.session_state.receitas:
        movimentos.append({**item, "tipo": "Receita"})
    for item in st.session_state.despesas:
        movimentos.append({**item, "tipo": "Despesa"})
    mov_df = pd.DataFrame(movimentos)
    if mov_df.empty:
        st.info("Nenhum lançamento cadastrado.")
    else:
        mov_df["data"] = pd.to_datetime(mov_df["data"])
        mov_df = mov_df.sort_values("data", ascending=False)
        st.dataframe(
            mov_df[["data", "tipo", "descricao", "categoria", "valor"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "tipo": "Tipo",
                "descricao": "Descrição",
                "categoria": "Categoria",
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            },
        )


elif pagina == "Receitas":
    header("Receitas", "Registre tudo o que entrou no seu negócio.")

    with st.form("nova_receita", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data_receita = c1.date_input("Data", value=date.today())
        valor_receita = c2.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
        descricao_receita = st.text_input("Descrição", placeholder="Ex.: venda para cliente")
        categoria_receita = st.selectbox("Categoria", ["Vendas", "Serviços", "Outras receitas"])
        salvar = st.form_submit_button("Adicionar receita", type="primary", use_container_width=True)

        if salvar:
            if valor_receita <= 0 or not descricao_receita.strip():
                st.error("Informe uma descrição e um valor maior que zero.")
            else:
                st.session_state.receitas.append(
                    {
                        "data": data_receita,
                        "descricao": descricao_receita.strip(),
                        "categoria": categoria_receita,
                        "valor": float(valor_receita),
                    }
                )
                st.success("Receita adicionada.")
                st.rerun()

    st.metric("Total de receitas", brl(total_receitas))
    if receitas.empty:
        st.info("Nenhuma receita cadastrada.")
    else:
        st.dataframe(
            receitas.sort_values("data", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "descricao": "Descrição",
                "categoria": "Categoria",
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            },
        )


elif pagina == "Despesas":
    header("Despesas", "Registre e organize os gastos do seu negócio.")

    with st.form("nova_despesa", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data_despesa = c1.date_input("Data", value=date.today(), key="data_despesa")
        valor_despesa = c2.number_input("Valor", min_value=0.0, step=10.0, format="%.2f", key="valor_despesa")
        descricao_despesa = st.text_input("Descrição", placeholder="Ex.: internet, fornecedor, combustível")
        categoria_despesa = st.selectbox(
            "Categoria",
            ["Fornecedores", "Serviços", "Aluguel", "Transporte", "Marketing", "Impostos", "Outras despesas"],
        )
        salvar = st.form_submit_button("Adicionar despesa", type="primary", use_container_width=True)

        if salvar:
            if valor_despesa <= 0 or not descricao_despesa.strip():
                st.error("Informe uma descrição e um valor maior que zero.")
            else:
                st.session_state.despesas.append(
                    {
                        "data": data_despesa,
                        "descricao": descricao_despesa.strip(),
                        "categoria": categoria_despesa,
                        "valor": float(valor_despesa),
                    }
                )
                st.success("Despesa adicionada.")
                st.rerun()

    st.metric("Total de despesas", brl(total_despesas))
    if despesas.empty:
        st.info("Nenhuma despesa cadastrada.")
    else:
        st.dataframe(
            despesas.sort_values("data", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "descricao": "Descrição",
                "categoria": "Categoria",
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            },
        )


elif pagina == "Fluxo de caixa":
    header("Fluxo de caixa", "Acompanhe entradas, saídas e saldo.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", brl(total_receitas))
    c2.metric("Saídas", brl(total_despesas))
    c3.metric("Saldo", brl(resultado))

    movimentos = []
    for item in st.session_state.receitas:
        movimentos.append({"data": item["data"], "descricao": item["descricao"], "entrada": item["valor"], "saida": 0.0})
    for item in st.session_state.despesas:
        movimentos.append({"data": item["data"], "descricao": item["descricao"], "entrada": 0.0, "saida": item["valor"]})

    fluxo = pd.DataFrame(movimentos)
    if fluxo.empty:
        st.info("Cadastre receitas e despesas para visualizar o fluxo de caixa.")
    else:
        fluxo["data"] = pd.to_datetime(fluxo["data"])
        fluxo = fluxo.sort_values("data")
        fluxo["saldo"] = (fluxo["entrada"] - fluxo["saida"]).cumsum()
        st.line_chart(fluxo.set_index("data")[["saldo"]])
        st.dataframe(fluxo.sort_values("data", ascending=False), use_container_width=True, hide_index=True)


elif pagina == "DAS":
    header("DAS", "Organize os pagamentos mensais do seu MEI.")
    st.info("Este módulo está na primeira versão. Aqui vamos incluir vencimentos, status de pagamento, histórico e alertas.")
    st.subheader("Próxima implementação")
    st.write("• calendário mensal do DAS\n\n• status: pendente, pago ou atrasado\n\n• comprovante de pagamento\n\n• alertas no dashboard")


elif pagina == "Declaração anual":
    header("Declaração anual", "Prepare as informações da DASN-SIMEI ao longo do ano.")
    st.info("O sistema vai consolidar faturamento e separar informações necessárias para facilitar a declaração anual.")
    st.metric("Faturamento registrado no sistema", brl(total_receitas))


elif pagina == "Documentos":
    header("Documentos", "Centralize comprovantes, notas e arquivos do negócio.")
    arquivo = st.file_uploader("Adicionar documento", type=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"])
    if arquivo is not None:
        st.success(f"Arquivo selecionado: {arquivo.name}")
        st.caption("Nesta versão o arquivo ainda não é persistido. O armazenamento será conectado ao banco de dados.")


elif pagina == "Meu MEI":
    header("Meu MEI", "Dados principais do seu negócio.")

    with st.form("dados_mei"):
        nome = st.text_input("Nome do negócio")
        cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
        atividade = st.text_input("Atividade principal")
        inicio = st.date_input("Data de abertura", value=date.today())
        enviado = st.form_submit_button("Salvar dados", type="primary")
        if enviado:
            st.success("Dados registrados nesta sessão. A persistência será adicionada com o banco de dados.")


st.divider()
st.caption("MEI Fácil • versão inicial em Streamlit")
