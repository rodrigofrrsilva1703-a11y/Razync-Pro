from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')
start=s.index('st.markdown("""\n<style>')
end=s.index('</style>\n""", unsafe_allow_html=True)', start)+len('</style>\n""", unsafe_allow_html=True)')
css='''st.markdown("""
<style>
:root{--rz-primary:#2563eb;--rz-bg:#f5f7fb;--rz-surface:#ffffff;--rz-text:#172033;--rz-muted:#667085;--rz-border:#e5e9f0}
.stApp{background:#f5f7fb;color:#172033}
[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #e5e9f0}
[data-testid="stSidebar"] .block-container{padding-top:1.2rem}
.block-container{padding-top:1.35rem;padding-bottom:2.5rem;max-width:1440px}
h1,h2,h3{color:#172033;letter-spacing:-.025em}
p,span,label{font-weight:400}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5e9f0;border-radius:12px;padding:16px 18px;box-shadow:0 1px 2px rgba(16,24,40,.03)}
[data-testid="stMetricLabel"]{color:#667085;font-size:.82rem}
[data-testid="stMetricValue"]{color:#172033;font-size:1.55rem;font-weight:750}
.rz-brand{font-size:1.45rem;font-weight:900;color:#172033;letter-spacing:-.045em}.rz-brand span{color:#2563eb}
.rz-kicker{color:#2563eb;font-weight:750;font-size:.72rem;margin-bottom:.15rem}
.rz-title{font-size:1.75rem;font-weight:800;color:#172033;margin:.05rem 0 .18rem;letter-spacing:-.035em}
.rz-sub{color:#667085;margin-bottom:1.2rem;font-size:.94rem}
.rz-alert{border-radius:10px;padding:12px 14px;margin-bottom:8px;background:#fff;border:1px solid #e5e9f0}
.rz-ok{border-left:3px solid #12b76a}.rz-info{border-left:3px solid #2e90fa}.rz-warn{border-left:3px solid #f79009}.rz-danger{border-left:3px solid #f04438}
.rz-small{color:#667085;font-size:.85rem;margin-top:2px}
.rz-section{font-size:1.02rem;font-weight:750;color:#172033;margin:.35rem 0 .65rem}
.rz-welcome{background:#fff;border:1px solid #e5e9f0;border-radius:14px;padding:18px 20px;margin-bottom:14px}
.rz-welcome-title{font-size:1.12rem;font-weight:750;color:#172033}.rz-welcome-sub{color:#667085;font-size:.88rem;margin-top:3px}
div[data-testid="stButton"] button,div[data-testid="stFormSubmitButton"] button{border-radius:9px;min-height:2.55rem;border:1px solid #d9e0ea;font-weight:650}
div[data-testid="stButton"] button:hover{border-color:#2563eb;color:#2563eb}
div[data-testid="stDataFrame"]{border:1px solid #e5e9f0;border-radius:10px;overflow:hidden;background:#fff}
[data-testid="stExpander"]{background:#fff;border:1px solid #e5e9f0;border-radius:10px}
[data-baseweb="select"]>div{border-radius:9px}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.22rem .35rem;border-radius:7px}
hr{border-color:#e5e9f0}
</style>
""", unsafe_allow_html=True)'''
s=s[:start]+css+s[end:]

old='''    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)\n    st.caption("Ecossistema Razync • Gestão completa do MEI")\n    st.divider()\n    groups = list(NAV_GROUPS.keys())'''
new='''    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)\n    st.caption("Gestão financeira e fiscal")\n    st.divider()\n    groups = list(NAV_GROUPS.keys())'''
s=s.replace(old,new,1)

old='''if page == "Dashboard":\n    header("Visão geral","Uma central contábil e financeira para acompanhar o seu MEI.")\n    c1,c2,c3,c4,c5 = st.columns(5)\n    c1.metric("Receita no ano",brl(year_revenue)); c2.metric("Despesas no ano",brl(year_expense)); c3.metric("Resultado estimado",brl(year_revenue-year_expense)); c4.metric("Limite utilizado",f"{limit_pct:.1f}%"); c5.metric("Documentos",len(docs))\n\n    st.subheader("Prioridades de hoje")'''
new='''if page == "Dashboard":\n    business_label = profile.get("trade_name") or profile.get("business_name") or "seu MEI"\n    header("Início", "Veja o que está acontecendo e o que precisa ser feito agora.")\n    st.markdown(f'<div class="rz-welcome"><div class="rz-welcome-title">{business_label}</div><div class="rz-welcome-sub">Resumo de {CURRENT_YEAR} • dados atualizados com seus lançamentos cadastrados</div></div>', unsafe_allow_html=True)\n    c1,c2,c3,c4 = st.columns(4)\n    c1.metric("Entradas",brl(year_revenue)); c2.metric("Saídas",brl(year_expense)); c3.metric("Resultado",brl(year_revenue-year_expense)); c4.metric("Limite MEI",f"{limit_pct:.1f}% usado")\n\n    st.markdown('<div class="rz-section">O que precisa da sua atenção</div>', unsafe_allow_html=True)'''
s=s.replace(old,new,1)
s=s.replace('    st.caption("Ações rápidas")','    st.markdown(\'<div class="rz-section">Ações rápidas</div>\', unsafe_allow_html=True)',1)
s=s.replace('        st.subheader("Faturamento por mês")','        st.markdown(\'<div class="rz-section">Entradas por mês</div>\', unsafe_allow_html=True)',1)
s=s.replace('        st.subheader("O que precisa de atenção")','        st.markdown(\'<div class="rz-section">Alertas</div>\', unsafe_allow_html=True)',1)
s=s.replace('    st.subheader("Últimos lançamentos")','    st.markdown(\'<div class="rz-section">Últimas movimentações</div>\', unsafe_allow_html=True)',1)
s=s.replace('    st.subheader("Saúde do seu MEI")','    st.markdown(\'<div class="rz-section">Organização do MEI</div>\', unsafe_allow_html=True)',1)
p.write_text(s,encoding='utf-8')
print('redesign applied')
