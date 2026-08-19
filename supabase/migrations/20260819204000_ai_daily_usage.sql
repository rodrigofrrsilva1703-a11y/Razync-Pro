create table if not exists public.ai_daily_usage (
    user_id integer not null references public.users(id) on delete cascade,
    usage_date date not null,
    request_count integer not null default 0 check (request_count >= 0),
    updated_at timestamptz not null default timezone('utc', now()),
    primary key (user_id, usage_date)
);

alter table public.ai_daily_usage enable row level security;

revoke all on table public.ai_daily_usage from anon;
revoke all on table public.ai_daily_usage from authenticated;

comment on table public.ai_daily_usage is
'Quota diaria persistente do Assistente Razync IA, contabilizada por usuario e data UTC.';
