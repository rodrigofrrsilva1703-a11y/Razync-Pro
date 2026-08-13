# Razync Pro

Plataforma em Streamlit para organização financeira e operacional de MEIs e pequenos negócios, dentro do ecossistema Razync.

## Funcionalidades

- Login e criação de conta
- Dados separados por usuário
- Dashboard com faturamento, despesas, resultado e alertas
- Receitas e despesas com categorias e exclusão
- Fluxo de caixa e exportação CSV
- Controle do DAS por competência
- Resumo anual para apoiar a organização da declaração
- Cofre de documentos no banco local
- Cadastro do MEI e limite anual configurável
- Assistente Razync baseado nos dados registrados
- Interface escura em preto e azul

## Executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Banco de dados

A versão atual usa SQLite (`razync_pro.db`) para desenvolvimento e validação do produto.

Para produção com múltiplos usuários, a próxima migração recomendada é PostgreSQL/Supabase, além de armazenamento externo para documentos.

## Segurança

As senhas são armazenadas com PBKDF2-HMAC-SHA256 e salt individual. Mesmo assim, esta é uma versão MVP e deve passar por revisão de segurança antes de uso comercial.

## Observação fiscal

O Razync Pro organiza dados informados pelo usuário. Valores de limite e outras regras sujeitas a mudanças são configuráveis e não são tratados como aconselhamento fiscal automático.
