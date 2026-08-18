# Razync Pro — Checklist de Produção

Execute este checklist no ambiente publicado antes de liberar uma versão comercial relevante.

## Inicialização

- [ ] `streamlit run app.py` inicia sem exceção.
- [ ] `requirements.txt` instala em Linux/Python suportado.
- [ ] logo e favicon carregam usando caminhos relativos do projeto.
- [ ] `.streamlit/config.toml` continua compatível com o Streamlit Cloud.
- [ ] nenhum caminho local do Windows é usado.

## Autenticação real

- [ ] cadastro cria usuário no Supabase Auth.
- [ ] e-mail de confirmação funciona.
- [ ] login confirmado funciona.
- [ ] recuperação de senha funciona.
- [ ] “Manter conectado” restaura a sessão após recarregar a página.
- [ ] logout remove sessão local e token persistente.

## Isolamento e dados

- [ ] duas contas diferentes não enxergam dados entre si.
- [ ] snapshot carrega somente dados do usuário autenticado.
- [ ] RLS permanece ativa nas tabelas de negócio.
- [ ] nenhum secret, service_role ou senha aparece no código ou nos logs.

## Storage

- [ ] upload de PDF funciona.
- [ ] download sob demanda funciona.
- [ ] exclusão remove o arquivo autorizado.
- [ ] arquivos não podem ser acessados por outra conta.

## Fluxos principais

- [ ] registrar, editar e excluir movimentação.
- [ ] recorrência gera ocorrência sem duplicar.
- [ ] importar CSV/XLSX e ignorar duplicidades quando solicitado.
- [ ] conciliação de nota funciona.
- [ ] DAS abre somente o endereço oficial configurado.
- [ ] upload/leitura assistida da guia DAS não altera dados sem confirmação.
- [ ] NFS-e importada não duplica número existente.
- [ ] fechamento mensal e PDFs são gerados.
- [ ] backup completo é preparado somente sob demanda.

## Tema e dispositivos

- [ ] tema claro sem áreas escuras indevidas.
- [ ] tema escuro sem gráficos claros indevidos.
- [ ] desktop 1366px sem sobreposição.
- [ ] tablet ~768px utilizável.
- [ ] celular ~390px com formulários, botões e cards legíveis.

## Operação

- [ ] backup automático do provedor está configurado.
- [ ] restauração foi testada em ambiente separado.
- [ ] monitoramento/alerta externo está configurado antes de escala.
- [ ] termos e política vigentes foram revisados.
- [ ] procedimento de exportação e exclusão de dados está documentado.
