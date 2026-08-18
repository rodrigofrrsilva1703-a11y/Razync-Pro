# Razync Pro

Razync Pro é uma plataforma em Streamlit focada em Microempreendedores Individuais (MEI), dentro do ecossistema Razync. O objetivo é centralizar organização financeira, fiscal e documental em uma interface simples e moderna.

## Acessar o Razync Pro

[🌐 Abrir o Razync Pro](https://razync-pro-je8appbtpfqcrg33nn6u5r8.streamlit.app/)

## Funcionalidades

- Login, cadastro, confirmação de e-mail e recuperação de senha com Supabase Auth
- Dados isolados por usuário
- Dashboard com receita, despesas, resultado, uso do limite e alertas
- Movimentações financeiras, recorrências, importação de extrato e conciliação
- Fluxo de caixa e análise financeira
- Relatório Mensal de Receitas Brutas e fechamento mensal
- Controle de notas fiscais e importação de NFS-e em CSV/XLSX
- Controle mensal do DAS e resumo anual para DASN-SIMEI
- Agenda de obrigações e central de notificações
- Cadastro de clientes, fornecedores e empregado
- Cofre de documentos em Supabase Storage privado
- Assistente Razync e Central de Automações
- Espaço do contador sem compartilhamento de senha
- Cadastro completo do MEI
- Backup e exportações
- Integrações e diagnóstico de infraestrutura

## Regras de MEI consideradas

O sistema foi estruturado para MEI optante pelo SIMEI, dentro do Simples Nacional. As regras legais são tratadas como parâmetros configuráveis porque podem mudar.

Na versão atual, o monitoramento usa como referência o limite vigente de R$ 81.000,00 por ano e R$ 6.750,00 por mês no ano de abertura. O Relatório Mensal, DAS e DASN-SIMEI são tratados como rotinas próprias do produto.

## Executar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sem `DATABASE_URL`, o sistema usa SQLite local para desenvolvimento:

```text
sqlite:///razync_pro.db
```

## Segurança e arquitetura

- Supabase Auth para identidades e sessões
- RLS por proprietário em todas as tabelas de negócio
- RPC de snapshot sem privilégio `SECURITY DEFINER`
- bucket privado com pasta exclusiva por usuário
- valores monetários armazenados como `Numeric(14,2)`
- migrações versionadas em `supabase/migrations`
- testes automatizados e validação contínua no GitHub Actions

Contas criadas antes do Supabase Auth são vinculadas com segurança no primeiro acesso confirmado usando o mesmo e-mail.

## Produção

A aplicação suporta PostgreSQL por meio da variável de ambiente `DATABASE_URL`.

Exemplo com PostgreSQL + psycopg:

```text
DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@HOST:5432/BANCO
```

Para Streamlit Community Cloud, configure `DATABASE_URL`, `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY` nos Secrets do aplicativo. Não coloque a senha do banco nem chaves secretas no repositório. Consulte `PRODUCTION_SETUP.md`.

## Banco de dados

A camada de persistência usa SQLAlchemy. Em desenvolvimento, SQLite é suficiente. Em produção, use PostgreSQL gerenciado, como Supabase/PostgreSQL compatível.

As principais tabelas incluem usuários, perfil do MEI, movimentações, recorrências, DAS, documentos, notas fiscais, contatos, empregado, obrigações e histórico de auditoria.

## Preparação comercial

O produto já possui autenticação, recuperação de senha, confirmação de e-mail, políticas de isolamento por usuário, armazenamento privado e registro de atividades. Antes de uma operação comercial em escala, mantenha revisão contínua de LGPD, termos de uso, política de privacidade, retenção de logs, backups automáticos, monitoramento e procedimentos de suporte.

## Observação fiscal

O Razync Pro organiza informações fornecidas pelo usuário e ajuda no acompanhamento das rotinas do MEI. Ele não substitui serviços oficiais do governo nem orientação profissional quando houver desenquadramento, pendências ou situações especiais.
