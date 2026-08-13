# Razync Pro

Razync Pro é uma plataforma em Streamlit focada em Microempreendedores Individuais (MEI), dentro do ecossistema Razync. O objetivo é centralizar organização financeira, fiscal e documental em uma interface simples e moderna.

## Funcionalidades

- Login e criação de conta
- Dados isolados por usuário
- Dashboard com receita, despesas, resultado, uso do limite e alertas
- Movimentações financeiras completas
- Relatório Mensal de Receitas Brutas
- Controle de notas fiscais emitidas
- Controle mensal do DAS
- Resumo anual para DASN-SIMEI
- Agenda de obrigações
- Cadastro de clientes e fornecedores
- Controle básico de empregado
- Cofre de documentos
- Assistente Razync com leitura dos dados cadastrados
- Cadastro completo do MEI
- Backup e exportação CSV

## Regras de MEI consideradas

O sistema foi estruturado para MEI optante pelo SIMEI, dentro do Simples Nacional. As regras legais são tratadas como parâmetros configuráveis porque podem mudar.

Na versão atual, o monitoramento usa como referência o limite vigente de R$ 81.000,00 por ano e R$ 6.750,00 por mês no ano de abertura. O Relatório Mensal, DAS e DASN-SIMEI são tratados como módulos próprios.

## Executar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sem `DATABASE_URL`, o sistema usa SQLite local para desenvolvimento:

```text
sqlite:///razync_pro.db
```

## Produção

A aplicação já suporta PostgreSQL para produção por meio da variável de ambiente `DATABASE_URL`.

Exemplo com PostgreSQL + psycopg:

```text
DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@HOST:5432/BANCO
```

Para Streamlit Community Cloud, configure `DATABASE_URL` nos Secrets do aplicativo. Não coloque credenciais no repositório.

## Banco de dados

A camada de persistência usa SQLAlchemy. Em desenvolvimento, SQLite é suficiente. Em produção, use PostgreSQL gerenciado, como Supabase/PostgreSQL compatível.

As tabelas incluem:

- usuários
- perfil do MEI
- movimentações
- DAS
- documentos
- notas fiscais
- clientes e fornecedores
- empregado
- obrigações

## Segurança

- Senhas com PBKDF2-HMAC-SHA256 e salt individual
- Credenciais de banco fora do repositório
- Separação dos dados por `user_id`
- Banco de produção configurável por variável de ambiente

Antes de uso comercial com dados reais, recomenda-se adicionar recuperação de senha, verificação de e-mail, política de privacidade, termos de uso, logs de auditoria, backups automáticos e revisão de LGPD.

## Observação fiscal

O Razync Pro organiza informações fornecidas pelo usuário e ajuda no acompanhamento das rotinas do MEI. Ele não substitui serviços oficiais do governo nem orientação profissional quando houver desenquadramento, pendências ou situações especiais.
