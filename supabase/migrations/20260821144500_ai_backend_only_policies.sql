create policy "ai_conversations_backend_only"
on public.ai_conversations
for all
to anon, authenticated
using (false)
with check (false);

create policy "ai_messages_backend_only"
on public.ai_messages
for all
to anon, authenticated
using (false)
with check (false);

create policy "ai_daily_usage_backend_only"
on public.ai_daily_usage
for all
to anon, authenticated
using (false)
with check (false);

comment on policy "ai_conversations_backend_only" on public.ai_conversations is
'Bloqueia acesso direto do cliente; o histórico é acessado somente pelo backend Razync.';
comment on policy "ai_messages_backend_only" on public.ai_messages is
'Bloqueia acesso direto do cliente; mensagens são acessadas somente pelo backend Razync.';
comment on policy "ai_daily_usage_backend_only" on public.ai_daily_usage is
'Bloqueia acesso direto do cliente; a quota é administrada somente pelo backend Razync.';

