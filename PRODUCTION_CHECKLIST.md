# Razync Pro — Checklist de Produção

Execute este checklist no ambiente publicado antes de liberar uma versão comercial relevante.

## Inicialização

- [ ] `streamlit run app.py` inicia sem exceção.
- [ ] `requirements.txt` instala em Linux/Python suportado.
- [ ] logo e favicon carregam usando caminhos relativos do projeto.
- [ ] `.streamlit/config.toml` continua compatível com o Streamlit Cloud.
- [ ] nenhum caminho local do Windows é usado.
- [ ] o deploy publicado abre sem erro de inicialização.

## Autenticação real

- [ ] cadastro cria usuário no Supabase Auth.
- [ ] e-mail de confirmação funciona.
- [ ] login confirmado funciona.
- [ ] recuperação de senha funciona.
- [ ] “Manter conectado” restaura a sessão após recarregar a página.
- [ ] logout remove sessão local e token persistente.
- [ ] acesso de desenvolvedor via GitHub continua restrito à conta autorizada.

## Isolamento e dados

- [ ] duas contas diferentes não enxergam dados entre si.
- [ ] snapshot carrega somente dados do usuário autenticado.
- [ ] RLS permanece ativa nas tabelas de negócio.
- [ ] nenhum secret, `service_role`, senha ou token aparece no código, interface ou logs.
- [ ] histórico de atividades não expõe conteúdo sensível de documentos nem credenciais.

## Storage

- [ ] upload de PDF funciona.
- [ ] download sob demanda funciona.
- [ ] exclusão remove o arquivo autorizado.
- [ ] arquivos não podem ser acessados por outra conta.
- [ ] a exclusão de conta remove também os objetos privados do usuário no Storage.

## Fluxos principais

- [ ] registrar, editar e excluir movimentação.
- [ ] desfazer exclusão de movimentação funciona durante a sessão.
- [ ] recorrência gera ocorrência sem duplicar.
- [ ] importar CSV/XLSX e ignorar duplicidades quando solicitado.
- [ ] conciliação de nota funciona.
- [ ] DAS abre somente o endereço oficial configurado.
- [ ] upload/leitura assistida da guia DAS não altera dados sem confirmação.
- [ ] NFS-e importada não duplica número existente.
- [ ] fechamento mensal e PDFs são gerados.
- [ ] backup completo do usuário é preparado somente sob demanda.
- [ ] Dashboard, Financeiro, Fiscal, Produtividade e Conta/Sistema abrem sem exceção.

## Conta e LGPD

- [ ] exportação/backup da conta pode ser gerado antes da exclusão.
- [ ] a tela de exclusão exige a confirmação exata e o aceite de irreversibilidade.
- [ ] a Edge Function `delete-account` exige JWT válido.
- [ ] a exclusão remove Storage privado, dados internos e identidade Supabase Auth.
- [ ] a chave administrativa usada pela Edge Function não existe nos Secrets do Streamlit.
- [ ] uma conta de teste excluída não consegue mais autenticar nem recuperar os dados removidos.

## Tema e dispositivos

- [ ] tema claro sem áreas escuras indevidas.
- [ ] tema escuro sem gráficos claros indevidos.
- [ ] desktop 1366px sem sobreposição.
- [ ] tablet ~768px utilizável.
- [ ] celular ~390px com formulários, botões e cards legíveis.
- [ ] sidebar, expanders e botões principais continuam utilizáveis por toque.

## Performance

- [ ] navegação comum usa o snapshot em sessão e não recarrega toda a base em cada clique.
- [ ] recorrências não consultam o banco desnecessariamente em todo rerun.
- [ ] documentos são baixados somente quando o usuário solicita.
- [ ] backup do usuário não é montado automaticamente ao abrir a página.
- [ ] telas principais continuam fluidas após carregar dados reais.

## IA Razync

- [ ] `OPENAI_API_KEY` está configurada somente nos Secrets do Streamlit.
- [ ] `OPENAI_MODEL` usa um modelo disponível para o projeto da API.
- [ ] o botão “Testar conexão da IA” retorna sucesso no ambiente publicado.
- [ ] respostas externas usam `store=False` e somente contexto agregado.
- [ ] CPF, CNPJ, credenciais, arquivos e descrições brutas não são enviados à IA.
- [ ] `OPENAI_DAILY_REQUEST_LIMIT` está definido conforme o orçamento desejado.
- [ ] ao atingir o limite ou ocorrer falha externa, o fallback local continua funcionando.

## Backup operacional

- [ ] backup automático/PITR do provedor está configurado quando disponível no plano.
- [ ] os Secrets `RAZYNC_BACKUP_DATABASE_URL`, `RAZYNC_BACKUP_SUPABASE_URL`, `RAZYNC_BACKUP_SUPABASE_SECRET_KEY` e `RAZYNC_BACKUP_PASSPHRASE` estão configurados no GitHub Actions quando o backup externo estiver habilitado.
- [ ] o workflow `production-backup.yml` gera somente artifact criptografado.
- [ ] a passphrase de restauração está guardada fora do GitHub.
- [ ] uma restauração completa foi testada em ambiente separado.
- [ ] o teste de restauração inclui PostgreSQL e documentos do Storage.

## Observabilidade e operação

- [ ] `APP_ENVIRONMENT` está configurado corretamente em produção.
- [ ] `SENTRY_DSN` está configurado quando observabilidade externa for exigida.
- [ ] eventos enviados ao monitoramento não contêm PII, tokens, cookies ou conteúdo de documentos.
- [ ] existem alertas para falhas repetidas de banco, Auth, Storage e disponibilidade.
- [ ] termos e política vigentes foram revisados.
- [ ] procedimento de exportação e exclusão de dados está documentado.
- [ ] procedimento de rollback para deploy/migração está conhecido e testado.

## Liberação

- [ ] `python -m compileall -q -x '^./scripts/' .` passa.
- [ ] `python -m unittest discover -s tests -v` passa integralmente.
- [ ] smoke test abre todas as páginas autenticadas sem exceção.
- [ ] nenhuma alteração crítica foi aplicada diretamente em produção sem branch/PR e revisão.
