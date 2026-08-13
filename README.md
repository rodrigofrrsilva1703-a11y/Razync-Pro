# MEI Fácil

Aplicação em Streamlit para ajudar microempreendedores individuais a organizar receitas, despesas, fluxo de caixa e informações importantes do negócio.

## Funcionalidades atuais

- Dashboard com faturamento, despesas, resultado e últimos lançamentos
- Gráfico mensal de receitas x despesas
- Cadastro persistente de receitas em SQLite
- Cadastro persistente de despesas em SQLite
- Exclusão de lançamentos
- Fluxo de caixa com saldo acumulado
- Cadastro dos dados do MEI
- Limite anual configurável para acompanhamento
- Estrutura inicial para DAS
- Estrutura inicial para declaração anual
- Área inicial de documentos

## Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

O banco `mei_facil.db` é criado automaticamente na primeira execução e não é versionado no GitHub.

> Importante: SQLite atende bem ao desenvolvimento local e ao MVP. Em hospedagens como o Streamlit Community Cloud, o armazenamento local pode ser reiniciado. Antes de colocar usuários reais no sistema, a persistência deve ser migrada para um banco externo, como Supabase/PostgreSQL.

## Próximos passos

1. Controle completo do DAS
2. Login e separação de dados por usuário
3. Migração para Supabase/PostgreSQL
4. Armazenamento permanente de documentos
5. Controle de faturamento anual e alertas
6. Assistente com IA
