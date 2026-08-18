from pathlib import Path

path = Path("app.py")
source = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global source
    if old not in source:
        raise SystemExit(f"Marcador não encontrado: {label}")
    source = source.replace(old, new, 1)


replace_once(
    "from onboarding_tools import onboarding_progress, recommended_setup\n",
    "from onboarding_tools import onboarding_progress, recommended_setup, first_session_plan\n",
    "onboarding import",
)
replace_once(
    "from sidebar_workspace import render_sidebar\n",
    "from sidebar_workspace import render_sidebar\n"
    "from productivity_workspace import render_productivity_workspace\n"
    "from account_workspace import render_account_workspace\n"
    "from fiscal_automation import analyze_das_guide\n"
    "from validators import valid_cnpj, valid_cpf, cpf_or_cnpj_status, valid_competence\n"
    "from commercial_readiness import PLAN_CATALOG, integration_maturity, production_checklist\n"
    "from monitoring import safe_error\n",
    "commercial imports",
)

replace_once(
    'except DatabaseConnectionError as exc:\n    st.error("Não foi possível conectar o Razync Pro ao banco definitivo.")',
    'except DatabaseConnectionError as exc:\n    safe_error("database_init_failed", exc, operation="init_db", backend="database")\n    st.error("Não foi possível conectar o Razync Pro ao banco definitivo.")',
    "database monitoring",
)

replace_once(
    'elif page == "Financeiro":\n',
    'elif page == "Produtividade":\n'
    '    header("Produtividade", "Automações, alertas e assistência em uma única área.")\n'
    '    render_productivity_workspace(navigate=navigate_to)\n\n'
    'elif page == "Conta e Sistema":\n'
    '    header("Conta e sistema", "Dados, privacidade, segurança e operação do Razync Pro.")\n'
    '    render_account_workspace(\n'
    '        navigate=navigate_to,\n'
    '        developer_access=st.session_state.get("auth_provider") == "github",\n'
    '    )\n\n'
    'elif page == "Financeiro":\n',
    "workspace routes",
)

replace_once(
    '        notes=st.text_area("Observações",key="das_notes")\n',
    '        if guide is not None:\n'
    '            guide_analysis = analyze_das_guide(guide.getvalue(), guide.name)\n'
    '            st.markdown("**Leitura assistida da guia**")\n'
    '            ga1, ga2, ga3 = st.columns(3)\n'
    '            ga1.metric("Competência", guide_analysis["competence"] or "Não encontrada")\n'
    '            ga2.metric("Valor provável", brl(guide_analysis["amount"]) if guide_analysis["amount"] is not None else "Não encontrado")\n'
    '            ga3.metric("Confiança", guide_analysis["confidence"])\n'
    '            if guide_analysis["competence"] and guide_analysis["competence"] != competence:\n'
    '                st.warning("A competência identificada no PDF é diferente da competência selecionada. Confira antes de salvar.")\n'
    '            for guide_warning in guide_analysis["warnings"]:\n'
    '                st.info(guide_warning)\n'
    '            st.caption("A leitura é apenas uma sugestão local. Valor, competência e pagamento só são gravados após sua confirmação.")\n'
    '        notes=st.text_area("Observações",key="das_notes")\n',
    "DAS assisted reading",
)

replace_once(
    '            if save:\n                if not name.strip(): st.error("Informe o nome do contato.")\n                else: add_contact(uid,contact_type=typ,name=name.strip(),document=doc.strip(),email=email.strip(),phone=phone.strip(),notes=notes.strip()); st.rerun()\n',
    '            if save:\n'
    '                document_ok, document_error = cpf_or_cnpj_status(doc)\n'
    '                if not name.strip():\n'
    '                    st.error("Informe o nome do contato.")\n'
    '                elif not document_ok:\n'
    '                    st.error(document_error)\n'
    '                else:\n'
    '                    add_contact(uid,contact_type=typ,name=name.strip(),document=doc.strip(),email=email.strip(),phone=phone.strip(),notes=notes.strip())\n'
    '                    st.rerun()\n',
    "contact validation",
)

replace_once(
    '            if save:\n                if not name.strip(): st.error("Informe o nome do empregado.")\n                else: add_employee(uid,name=name.strip(),cpf=cpf.strip(),admission_date=admission,salary=salary,status=status,notes=notes.strip()); st.rerun()\n',
    '            if save:\n'
    '                if not name.strip():\n'
    '                    st.error("Informe o nome do empregado.")\n'
    '                elif cpf.strip() and not valid_cpf(cpf):\n'
    '                    st.error("CPF inválido.")\n'
    '                else:\n'
    '                    add_employee(uid,name=name.strip(),cpf=cpf.strip(),admission_date=admission,salary=salary,status=status,notes=notes.strip())\n'
    '                    st.rerun()\n',
    "employee validation",
)

replace_once(
    '        valid_reference = not reference.strip() or bool(__import__("re").fullmatch(r"20\\d{2}-(0[1-9]|1[0-2])", reference.strip()))\n',
    '        valid_reference = not reference.strip() or valid_competence(reference.strip())\n',
    "competence validation",
)

old_mei = '        if st.form_submit_button("Salvar dados",width="stretch"): save_profile(uid,cnpj=cnpj,business_name=business,trade_name=trade,main_activity=activity,activity_type=activity_type,opening_date=opening_date,annual_limit=annual_limit,city=city,state=state.upper(),phone=phone,municipal_registration=municipal,state_registration=state_reg,has_employee=has_employee); st.success("Dados salvos."); st.rerun()\n'
new_mei = '        if st.form_submit_button("Salvar dados",width="stretch"):\n            if cnpj.strip() and not valid_cnpj(cnpj):\n                st.error("CNPJ inválido. Confira os 14 dígitos antes de salvar.")\n            else:\n                save_profile(uid,cnpj=cnpj,business_name=business,trade_name=trade,main_activity=activity,activity_type=activity_type,opening_date=opening_date,annual_limit=annual_limit,city=city,state=state.upper(),phone=phone,municipal_registration=municipal,state_registration=state_reg,has_employee=has_employee)\n                st.success("Dados salvos.")\n                st.rerun()\n'
replace_once(old_mei, new_mei, "MEI validation")

replace_once(
    '                st.caption(f"{item[\'status\']} · {item[\'mode\']}")\n',
    '                st.caption(f"{integration_maturity(item)} · {item[\'mode\']} · {item[\'status\']}")\n',
    "integration maturity",
)

replace_once(
    '    st.write("✓ Organização financeira e fiscal")\n    st.write("✓ Importação de extrato e NFS-e")\n    st.write("✓ Alertas, relatórios, documentos e backup")\n',
    '    plan_name = "Pro" if st.session_state.get("auth_provider") == "github" else "Essencial"\n'
    '    plan = PLAN_CATALOG[plan_name]\n'
    '    st.caption(plan["description"])\n'
    '    for feature in plan["features"]:\n'
    '        st.write(f"✓ {feature}")\n'
    '    st.caption("Preços não ficam fixos no código; o checkout comercial é configurado por ambiente.")\n',
    "plan catalog",
)

replace_once(
    '    st.write("○ **Integrações bancárias diretas** — importação inteligente de arquivo já disponível")\n',
    '    st.write("○ **Integrações bancárias diretas** — importação inteligente de arquivo já disponível")\n'
    '    section("Prontidão de produção")\n'
    '    readiness = production_checklist(\n'
    '        persistent_db=runtime["persistent"],\n'
    '        auth_ready=is_supabase_auth_configured(),\n'
    '        storage_ready=bool(secret_value("SUPABASE_URL") and secret_value("SUPABASE_PUBLISHABLE_KEY")),\n'
    '        session_secret=bool(secret_value("SESSION_COOKIE_SECRET")),\n'
    '    )\n'
    '    for check in readiness:\n'
    '        marker = "✓" if check["ok"] else "○"\n'
    '        st.write(f"{marker} **{check[\'item\']}** — {check[\'detail\']}")\n',
    "production checklist UI",
)

replace_once(
    '    section("2. Próximas etapas")\n    progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))\n',
    '    section("2. Próximas etapas")\n'
    '    progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))\n'
    '    st.caption("Roteiro recomendado para os primeiros minutos no Razync.")\n'
    '    for setup_item in first_session_plan(progress):\n'
    '        if not setup_item["done"]:\n'
    '            st.write(f"○ **{setup_item[\'title\']}** — {setup_item[\'detail\']}")\n',
    "onboarding plan",
)

path.write_text(source, encoding="utf-8")
print("Commercial readiness patch applied")
