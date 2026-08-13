# MEI Fácil

Aplicação em Streamlit para ajudar microempreendedores individuais a organizar a rotina financeira e acompanhar obrigações básicas do negócio.

## Funcionalidades atuais

- Dashboard com receitas, despesas e resultado estimado
- Cadastro de receitas
- Cadastro de despesas
- Fluxo de caixa
- Estrutura inicial para DAS
- Estrutura inicial para declaração anual
- Upload de documentos em modo demonstrativo
- Cadastro dos dados do MEI em modo demonstrativo

> Nesta primeira versão, os dados ficam apenas na sessão do Streamlit. Persistência em banco de dados será adicionada nas próximas etapas.

## Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Próximos passos

1. Banco de dados e autenticação
2. Persistência de receitas e despesas
3. Controle de DAS
4. Controle de faturamento e alertas
5. Documentos persistentes
6. Assistente com IA
