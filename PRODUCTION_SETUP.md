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
SENTRY_DSN = "https://..." # opcional, para observabilidade externa
APP_ENVIRONMENT = "production"
OPENAI_API_KEY = "sk-proj-..." # opcional, ativa a IA do Assistente Razync
OPENAI_MODEL = "gpt-5.6-luna" # opcional; modelo com foco em custo
```

Use somente a chave publicável no Streamlit; nunca configure `service_role` ou secret key administrativa no aplicativo. O `SESSION_COOKIE_SECRET` cifra o refresh token salvo no navegador para a opção “Manter conectado”.

4. Salve e reinicie o aplicativo.

Depois do reinício, abra no Razync Pro:

`Conta e sistema → Status do sistema`

O banco deve aparecer como `PostgreSQL`, com persistência ativa.

## 3. Contas, autenticação e exclusão

O ambiente de produção usa Supabase Auth para login, confirmação de e-mail, recuperação de senha e renovação de sessão. Contas legadas podem ser vinculadas à identidade confirmada usando o mesmo e-mail, preservando os dados existentes.

A exclusão de conta é executada pela Edge Function protegida `delete-account`, com JWT obrigatório. Ela remove primeiro os documentos privados, depois o registro interno do usuário (cascateando os dados de negócio) e por último a identidade Supabase Auth. A chave administrativa permanece somente no ambiente seguro da Edge Function.

Enquanto as variáveis de Auth não estiverem configuradas, o aplicativo informa explicitamente que está em modo temporário de desenvolvimento/migração. Esse modo não deve ser usado para clientes reais.


## Assistente Razync com IA

O Assistente Razync usa a OpenAI Responses API somente quando `OPENAI_API_KEY` estiver configurada. Sem a chave, o sistema preserva o assistente local baseado em regras, evitando indisponibilidade do recurso.

A integração envia apenas um contexto agregado calculado a partir do snapshot já carregado na sessão. Não são enviados CNPJ, CPF, telefone, nomes de clientes/fornecedores, números de documentos, arquivos, tokens, credenciais ou conteúdo bruto de documentos. A chamada usa `store=False`.

A chave da OpenAI deve existir somente nos Secrets do ambiente. Nunca a grave no repositório, no navegador ou em logs. O modelo pode ser alterado por `OPENAI_MODEL`; o padrão do produto é `gpt-5.6-luna` para equilibrar qualidade e custo.

O assistente é consultivo: ele não paga DAS, transmite declarações, emite notas ou altera dados por conta própria. Regras fiscais e prazos sujeitos a mudança devem ser confirmados em fonte oficial.

## 4. Segurança e privacidade

Nunca publique a string real de conexão, segredos de sessão ou chaves privadas em arquivos do repositório. O arquivo `.streamlit/secrets.toml` deve permanecer ignorado pelo Git.

Antes de ampliar o uso comercial, revise periodicamente:

- políticas RLS e permissões do Storage;
- política de privacidade e termos de uso;
- retenção e exclusão de documentos;
- logs de auditoria e controles de acesso;
- LGPD e procedimentos de atendimento ao titular;
- backups automáticos, restauração e monitoramento de disponibilidade.

## 5. Documentos

Novos documentos de contas autenticadas são gravados no bucket privado `documents`, em uma pasta exclusiva do usuário. O PostgreSQL mantém metadados e o caminho do arquivo. Arquivos legados continuam disponíveis durante a transição quando aplicável.

## 6. Operação, backup e recuperação

O projeto possui duas camadas complementares de proteção:

1. **Backup do provedor:** use o backup diário/PITR oferecido pelo plano Supabase quando disponível.
2. **Backup externo criptografado:** o workflow `.github/workflows/production-backup.yml` gera diariamente um `pg_dump` mais os objetos do bucket `documents`, criptografa o pacote com AES-GCM e publica somente o arquivo cifrado como artifact temporário do GitHub Actions.

Para habilitar o workflow externo, configure estes Repository Secrets no GitHub:

```text
RAZYNC_BACKUP_DATABASE_URL
RAZYNC_BACKUP_SUPABASE_URL
RAZYNC_BACKUP_SUPABASE_SECRET_KEY
RAZYNC_BACKUP_PASSPHRASE
```

A secret key de backup fica somente no GitHub Actions e nunca entra no Streamlit ou no repositório. Use uma passphrase longa, exclusiva e guardada fora do GitHub; sem ela o backup criptografado não pode ser restaurado.

Além disso:

- Migrações versionadas ficam em `supabase/migrations`.
- Execute a suíte de testes antes de qualquer merge ou publicação relevante.
- Verifique periodicamente os Security e Performance Advisors do provedor.
- Teste a restauração em ambiente separado de forma periódica.
- O ZIP de backup do usuário é uma cópia portátil; ele não substitui o backup operacional.
- Não execute comandos destrutivos de reset no projeto de produção.
- Mantenha um plano de rollback para alterações de banco e autenticação.

## 7. Monitoramento externo

O módulo `monitoring.py` integra opcionalmente com Sentry quando `SENTRY_DSN` estiver configurado. O SDK é inicializado com `send_default_pii=False`, remove request, usuário, breadcrumbs, extras e contextos customizados antes do envio, e mantém os logs estruturados locais como fallback.

Não envie para observabilidade CPF/CNPJ, nomes, e-mails, telefone, tokens, conteúdo de documentos ou descrições financeiras livres. Configure alertas externos para falhas de banco, Auth, Storage, importação e disponibilidade.

Consulte `OPERATIONS_RUNBOOK.md` para procedimento de incidente.

## 8. Integrações externas

A importação de extratos CSV/Excel e de arquivos de NFS-e já funciona sem credenciais bancárias. Integração direta com bancos, envio automatizado de mensagens e emissão direta de NFS-e dependem de provedores/APIs e credenciais específicas; não devem ser apresentadas como conectadas quando não estiverem configuradas.

A interface classifica integrações como **Ativo**, **Assistido** ou **Configurar**, evitando apresentar uma capacidade assistida como integração automática.

## 9. Validação antes da liberação

Execute `PRODUCTION_CHECKLIST.md` no ambiente publicado, incluindo login real, recuperação de senha, upload/download, isolamento entre contas, tema claro/escuro, exclusão de uma conta de teste e teste em celular/tablet/desktop.
