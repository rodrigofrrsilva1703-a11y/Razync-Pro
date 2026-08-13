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

4. Salve e reinicie o aplicativo.

Depois do reinício, abra no Razync Pro:

`Configurações → Status do Sistema`

O banco deve aparecer como `PostgreSQL`, com persistência ativa.

## 3. Segurança

Nunca publique a string real de conexão em arquivos do repositório. O arquivo `.streamlit/secrets.toml` está ignorado pelo Git.

Antes de abrir o sistema para clientes reais, reative autenticação, recuperação de senha e isolamento por conta, e revise política de privacidade, termos de uso, retenção de documentos, logs e controles de acesso.

## 4. Documentos

O banco atual pode armazenar documentos em binário, mas para escala comercial recomenda-se usar um storage dedicado e manter no PostgreSQL apenas metadados e referências. Isso evita crescimento excessivo do banco principal.

## 5. Integrações externas

A importação de extratos CSV/Excel já é funcional sem credenciais externas. Integração direta com bancos e automação de NFS-e dependem de provedores/APIs e credenciais específicas; não devem ser simuladas como se estivessem conectadas.
