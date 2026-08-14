# Razync Pro — Configuração de Produção

O código do Razync Pro já aceita PostgreSQL por `DATABASE_URL`. Sem essa configuração, o sistema usa um banco SQLite temporário apenas para desenvolvimento e testes.

## 1. Banco PostgreSQL / Supabase

Crie um projeto PostgreSQL gerenciado (por exemplo, Supabase) e copie a string de conexão.

Formato aceito:

```text
postgresql://USUARIO:SENHA@HOST:5432/BANCO
```

O Razync Pro converte automaticamente para o driver `psycopg` utilizado no projeto.

## 2. Streamlit Community Cloud

No painel do aplicativo:

1. Abra `Manage app`.
2. Entre em `Settings` / `Secrets`.
3. Adicione:

```toml
DATABASE_URL = "postgresql://USUARIO:SENHA@HOST:5432/BANCO"
```

4. Adicione também:

```toml
SUPABASE_URL = "https://etimfgenlludorrftapb.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_..."
SESSION_COOKIE_SECRET = "gere-um-valor-aleatorio-com-pelo-menos-32-caracteres"
```

Use somente a chave publicável; nunca configure `service_role` no aplicativo. O `SESSION_COOKIE_SECRET` cifra o refresh token salvo no navegador para a opção “Manter conectado”; use um valor aleatório exclusivo e nunca o publique.

5. Salve e reinicie o aplicativo.

Depois do reinício, abra no Razync Pro:

`Configurações → Status do Sistema`

O banco deve aparecer como `PostgreSQL`, com persistência ativa.

## 3. Migração das contas existentes

As contas antigas são preservadas. Cada usuário deve criar/confirmar a identidade no Supabase Auth usando o mesmo e-mail. No primeiro login confirmado, a identidade é vinculada ao cadastro existente sem mover ou apagar os dados.

Enquanto as variáveis de Auth não estiverem configuradas, o aplicativo mostra explicitamente o modo temporário de migração.

## 4. Segurança

Nunca publique a string real de conexão em arquivos do repositório. O arquivo `.streamlit/secrets.toml` está ignorado pelo Git.

Antes de abrir o sistema para clientes reais, reative autenticação, recuperação de senha e isolamento por conta, e revise política de privacidade, termos de uso, retenção de documentos, logs e controles de acesso.

## 5. Documentos

Novos documentos de contas autenticadas são gravados no bucket privado `documents`, em uma pasta exclusiva do usuário. O PostgreSQL mantém apenas metadados e o caminho. Arquivos legados continuam disponíveis durante a transição.

## 6. Operação e recuperação

- Migrações versionadas ficam em `supabase/migrations`.
- Execute os testes antes de qualquer merge.
- Verifique periodicamente os Security e Performance Advisors.
- Teste a restauração de backup em ambiente separado.
- Não execute `db reset --linked` no projeto de produção.

## 7. Integrações externas

A importação de extratos CSV/Excel já é funcional sem credenciais externas. Integração direta com bancos e automação de NFS-e dependem de provedores/APIs e credenciais específicas; não devem ser simuladas como se estivessem conectadas.
