from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_demo() -> None:
    st.markdown("### Demonstração segura")
    st.caption("Dados fictícios — nada é salvo e nenhuma conta é necessária.")
    revenue, expenses, balance = 18450.0, 6270.0, 12180.0
    a,b,c=st.columns(3)
    a.metric("Receitas no ano", f"R$ {revenue:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    b.metric("Despesas no ano", f"R$ {expenses:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c.metric("Resultado", f"R$ {balance:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    data=pd.DataFrame({
        "Mês":["Mar","Abr","Mai","Jun","Jul","Ago"],
        "Receitas":[2100,2800,2400,3600,3350,4200],
        "Despesas":[900,760,1050,1120,1180,1260],
    })
    fig=px.bar(data,x="Mês",y=["Receitas","Despesas"],barmode="group",color_discrete_sequence=["#08b9ef","#607487"])
    fig.update_layout(height=310,margin=dict(l=8,r=8,t=18,b=8),legend_title_text="",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,width="stretch")
    st.info("Próximo vencimento fictício: DAS de 08/2026 em 21/09/2026.")
    st.success("Saúde do MEI fictício: boa — faturamento em 22,8% do limite anual.")
    if st.button("Voltar para entrar",width="stretch"):
        st.session_state.pop("_demo_mode",None)
        st.rerun()
