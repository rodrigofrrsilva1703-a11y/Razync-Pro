# Razync Pro — Configuração de Produção

O código do Razync Pro aceita PostgreSQL por `DATABASE_URL`. Sem essa configuração, o sistema usa SQLite apenas para desenvolvimento e testes.

## 1. Banco PostgreSQL / Supabase

Crie um projeto PostgreSQL gerenciado, como Supabase, e copie a string de conexão.

Formato aceito:

```text
postgresql://USUARIO:SENHA@HOST:5432/BANCO
```

O Razync Pro converte automaticamente a conexão para o driver `psycopg` utilizado no projeto.

## 2. Streamlit Community Cloud

No painel do aplicativo:

1. Abra `Manage app`.
2. Entre em `Settings` / `Secrets`.
3. Configure:

```toml
DATABASE_URL = "postgresql://USUARIO:SENHA@HOST:5432/BANCO"
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_..."
SESSION_COOKIE_SECRET = "gere-um-valor-aleatorio-com-pelo-menos-32-caracteres"
```

Use somente a chave publicável; nunca configure `service_role` no aplicativo. O `SESSION_COOKIE_SECRET` cifra o refresh token salvo no navegador para a opção “Manter conectado”; use um valor aleatório exclusivo e nunca o publique.

4. Salve e reinicie o aplicativo.

Depois do reinício, abra no Razync Pro:

`Conta e sistema → Status do sistema`

O banco deve aparecer como `PostgreSQL`, com persistência ativa.

## 3. Contas e autenticação

O ambiente de produção usa Supabase Auth para login, confirmação de e-mail, recuperação de senha e renovação de sessão. Contas legadas podem ser vinculadas à identidade confirmada usando o mesmo e-mail, preservando os dados existentes.

Enquanto as variáveis de Auth não estiverem configuradas, o aplicativo informa explicitamente que está em modo temporário de desenvolvimento/migração. Esse modo não deve ser usado para clientes reais.

## 4. Segurança e privacidade

Nunca publique a string real de conexão, segredos de sessão ou chaves privadas em arquivos do repositório. O arquivo `.streamlit/secrets.toml` deve permanecer ignorado pelo Git.

Antes de ampliar o uso comercial, revise periodicamente:

- políticas RLS e permissões do Storage;
- política de privacidade e termos de uso;
- retenção e exclusão de documentos;
- logs de auditoria e controles de acesso;
- LGPD e procedimentos de atendimento ao titular;
- backups automáticos, restauração e monitoramento de disponibilidade.

A exclusão de usuário do Supabase Auth exige privilégio administrativo e não deve ser executada com `service_role` dentro do Streamlit. Use backend seguro/Edge Function ou processo administrativo autorizado.

## 5. Documentos

Novos documentos de contas autenticadas são gravados no bucket privado `documents`, em uma pasta exclusiva do usuário. O PostgreSQL mantém metadados e o caminho do arquivo. Arquivos legados continuam disponíveis durante a transição quando aplicável.

## 6. Operação, backup e recuperação

- Migrações versionadas ficam em `supabase/migrations`.
- Execute a suíte de testes antes de qualquer merge ou publicação relevante.
- Verifique periodicamente os Security e Performance Advisors do provedor.
- Configure backup automático do banco usando os recursos do provedor e uma política de retenção documentada.
- Garanta que documentos do Storage façam parte do plano de recuperação.
- Teste a restauração em ambiente separado de forma periódica.
- O ZIP de backup do usuário é uma cópia portátil; ele não substitui o backup operacional de banco e Storage.
- Não execute comandos destrutivos de reset no projeto de produção.
- Mantenha um plano de rollback para alterações de banco e autenticação.

## 7. Monitoramento

O módulo `monitoring.py` gera eventos operacionais seguros e não deve receber PII, tokens ou conteúdo de documentos. Antes de escalar comercialmente, conecte os logs do ambiente a um serviço de observabilidade e crie alertas para falhas de banco, Auth, Storage, importação e disponibilidade.

Consulte `OPERATIONS_RUNBOOK.md` para procedimento de incidente.

## 8. Integrações externas

A importação de extratos CSV/Excel e de arquivos de NFS-e já funciona sem credenciais bancárias. Integração direta com bancos, envio automatizado de mensagens e emissão direta de NFS-e dependem de provedores/APIs e credenciais específicas; não devem ser apresentadas como conectadas quando não estiverem configuradas.

A interface classifica integrações como **Ativo**, **Assistido** ou **Configurar**, evitando apresentar uma capacidade assistida como integração automática.

## 9. Validação antes da liberação

Execute `PRODUCTION_CHECKLIST.md` no ambiente publicado, incluindo login real, recuperação de senha, upload/download, isolamento entre contas, tema claro/escuro e teste em celular/tablet/desktop.