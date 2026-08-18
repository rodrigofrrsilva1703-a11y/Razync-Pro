from pathlib import Path
p=Path('app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('from workspace_style import inject_workspace_style\n','from workspace_style import inject_workspace_style\nfrom dashboard_workspace import render_dashboard_workspace\n',1)
start=s.index('# Dashboard metrics are calculated from the local snapshot')
end=s.index('elif page == "Financeiro":', start)
new='''# Dashboard V2 uses only the local snapshot while navigating.\nif page == "Dashboard":\n    business_label = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"\n    cnpj_label = str(profile.get("cnpj") or "").strip() or None\n    header("Visão geral", "O que importa hoje para manter seu MEI organizado.")\n    business_card(business_label, CURRENT_YEAR, cnpj_label)\n    render_dashboard_workspace(\n        profile=profile, transactions=transactions, invoices=invoices,\n        das_rows=das_rows, obligations=obligations, documents=docs,\n        annual_limit=limit, annual_revenue=year_revenue, current_year=CURRENT_YEAR,\n        brl=brl, navigate=navigate_to,\n    )\n\n'''
s=s[:start]+new+s[end:]
p.write_text(s,encoding='utf-8')
print('Dashboard V2 integrated')
