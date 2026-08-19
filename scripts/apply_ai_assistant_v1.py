from pathlib import Path


APP = Path("app.py")
text = APP.read_text(encoding="utf-8")

import_anchor = "from account_workspace import render_account_workspace\n"
import_line = "from assistant_workspace import render_ai_assistant\n"
if import_line not in text:
    if import_anchor not in text:
        raise SystemExit("anchor de importacao nao encontrado")
    text = text.replace(import_anchor, import_anchor + import_line, 1)

old_block = '''elif page == "Assistente Razync":
    header("Assistente Razync","Faça perguntas simples sobre os dados que já estão no sistema.")
    prompts=["Quanto ainda posso faturar?","Compare este mês com o anterior","Qual foi minha maior despesa?","Quanto faturei no trimestre?","Tenho documentos faltando?","Qual é o próximo vencimento?","Tenho DAS atrasado?","Como estão minhas notas?"]
    q=st.text_input("Pergunte sobre seu MEI",placeholder="Ex.: Quanto ainda posso faturar neste ano?")
    choice=st.selectbox("Ou escolha uma pergunta",["Escolha..."]+prompts)
    if choice!="Escolha...": q=choice
    if q:
        st.success(assistant_answer(q, transactions, invoices, das_rows, limit, CURRENT_YEAR, obligations=obligations, documents=docs))
    st.caption("As respostas usam os registros do Razync Pro e não substituem análise profissional ou consulta aos portais oficiais.")
'''

new_block = '''elif page == "Assistente Razync":
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
'''

if old_block in text:
    text = text.replace(old_block, new_block, 1)
elif new_block not in text:
    raise SystemExit("bloco do Assistente Razync nao encontrado")
APP.write_text(text, encoding="utf-8")

setup = Path("PRODUCTION_SETUP.md")
setup_text = setup.read_text(encoding="utf-8")
secret_anchor = 'APP_ENVIRONMENT = "production"\n'
secret_addition = 'OPENAI_API_KEY = "sk-proj-..." # opcional, ativa a IA do Assistente Razync\nOPENAI_MODEL = "gpt-5.6-luna" # opcional; modelo com foco em custo\n'
if "OPENAI_API_KEY" not in setup_text:
    if secret_anchor not in setup_text:
        raise SystemExit("anchor de secrets nao encontrado")
    setup_text = setup_text.replace(secret_anchor, secret_anchor + secret_addition, 1)

ai_section = '''\n## Assistente Razync com IA\n\nO Assistente Razync usa a OpenAI Responses API somente quando `OPENAI_API_KEY` estiver configurada. Sem a chave, o sistema preserva o assistente local baseado em regras, evitando indisponibilidade do recurso.\n\nA integração envia apenas um contexto agregado calculado a partir do snapshot já carregado na sessão. Não são enviados CNPJ, CPF, telefone, nomes de clientes/fornecedores, números de documentos, arquivos, tokens, credenciais ou conteúdo bruto de documentos. A chamada usa `store=False`.\n\nA chave da OpenAI deve existir somente nos Secrets do ambiente. Nunca a grave no repositório, no navegador ou em logs. O modelo pode ser alterado por `OPENAI_MODEL`; o padrão do produto é `gpt-5.6-luna` para equilibrar qualidade e custo.\n\nO assistente é consultivo: ele não paga DAS, transmite declarações, emite notas ou altera dados por conta própria. Regras fiscais e prazos sujeitos a mudança devem ser confirmados em fonte oficial.\n'''
if "## Assistente Razync com IA" not in setup_text:
    marker = "## 4. Segurança e privacidade"
    if marker not in setup_text:
        raise SystemExit("anchor da documentacao de IA nao encontrado")
    setup_text = setup_text.replace(marker, ai_section + "\n" + marker, 1)
setup.write_text(setup_text, encoding="utf-8")

readme = Path("README.md")
readme_text = readme.read_text(encoding="utf-8")
old_feature = "- Assistente Razync e Central de Automações"
new_feature = "- Assistente Razync com IA opcional via OpenAI, contexto agregado e fallback local"
if old_feature in readme_text:
    readme_text = readme_text.replace(old_feature, new_feature, 1)
elif new_feature not in readme_text:
    raise SystemExit("bullet do assistente no README nao encontrado")
readme.write_text(readme_text, encoding="utf-8")

print("Assistente Razync IA V1 aplicado")
