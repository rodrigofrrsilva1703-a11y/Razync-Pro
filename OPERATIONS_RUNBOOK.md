# Razync Pro — Runbook de Operação

Este documento complementa `PRODUCTION_SETUP.md` e descreve práticas para operação comercial sem colocar segredos administrativos dentro do Streamlit.

## Backups e restauração

- Mantenha backups automáticos do PostgreSQL/Supabase conforme os recursos do provedor.
- Mantenha política de retenção documentada e adequada ao plano contratado.
- Documentos ficam no Storage privado e devem entrar no plano de recuperação.
- Execute teste de restauração em projeto/ambiente separado antes de considerar a rotina confiável.
- O backup gerado pelo usuário no Razync é uma cópia portátil dos dados da conta; ele não substitui o backup operacional do banco e Storage.
- Nunca execute reset destrutivo no projeto de produção para testar restauração.

## Monitoramento

O módulo `monitoring.py` aceita somente campos operacionais em lista permitida. Não envie para logs:

- CPF/CNPJ;
- e-mail, telefone ou nome;
- access token, refresh token, cookies ou secrets;
- conteúdo ou nome sensível de documentos;
- descrições financeiras livres do usuário.

Antes de escalar comercialmente, conecte os logs do ambiente a um provedor de observabilidade e configure alertas para:

- falhas repetidas de banco;
- falhas de Supabase Auth e Storage;
- tempo de resposta anormal;
- exceções de importação;
- indisponibilidade do Streamlit Cloud.

## LGPD e atendimento ao titular

O produto deve oferecer ao usuário caminho claro para:

- corrigir dados cadastrais;
- exportar seus dados por backup;
- consultar política e termos vigentes;
- solicitar exclusão de conta e dados.

A exclusão da identidade do Supabase Auth não deve usar `service_role` dentro do Streamlit. Em produção, implemente o procedimento administrativo em backend seguro/Edge Function ou processo operacional com autorização adequada.

## Incidentes

1. Preserve evidências técnicas sem copiar dados pessoais desnecessariamente.
2. Identifique a versão/commit em produção.
3. Verifique Status do Sistema, banco, Auth e Storage.
4. Se a falha veio de deploy, reverta para o último commit validado.
5. Não corrija produção diretamente sem passar por testes e diff.
6. Registre causa, impacto e ação preventiva.

## Alterações de banco

- Toda alteração deve ser versionada em `supabase/migrations`.
- Revise RLS e grants junto com qualquer nova tabela.
- Teste migração e rollback em ambiente separado.
- Evite alterações destrutivas sem cópia recuperável.
