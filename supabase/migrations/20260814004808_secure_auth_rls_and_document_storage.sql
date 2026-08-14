-- Applied to project etimfgenlludorrftapb as migration 20260814004808.
-- Links legacy integer users to Supabase Auth without deleting existing accounts.
alter table public.users
  add column if not exists auth_user_id uuid unique references auth.users(id) on delete set null;

alter table public.documents add column if not exists storage_path text;
alter table public.documents alter column content drop not null;

revoke all on function public.razync_user_snapshot(bigint) from public, anon, authenticated;
alter function public.razync_user_snapshot(bigint) security invoker;

drop policy if exists users_own_row on public.users;
create policy users_own_row on public.users for all to authenticated
  using ((select auth.uid()) = auth_user_id)
  with check ((select auth.uid()) = auth_user_id);

do $migration$
declare table_name text;
begin
  foreach table_name in array array[
    'mei_profiles','transactions','das_items','documents',
    'invoices','contacts','employees','obligations'
  ]
  loop
    execute format('drop policy if exists %I on public.%I', table_name || '_owner', table_name);
    execute format(
      'create policy %I on public.%I for all to authenticated
       using (exists (select 1 from public.users u where u.id = %I.user_id and u.auth_user_id = (select auth.uid())))
       with check (exists (select 1 from public.users u where u.id = %I.user_id and u.auth_user_id = (select auth.uid())))',
      table_name || '_owner', table_name, table_name, table_name
    );
  end loop;
end
$migration$;

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do update set public = false;

drop policy if exists documents_storage_select on storage.objects;
create policy documents_storage_select on storage.objects for select to authenticated
  using (bucket_id = 'documents' and (storage.foldername(name))[1] = (select auth.uid())::text);
drop policy if exists documents_storage_insert on storage.objects;
create policy documents_storage_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'documents' and (storage.foldername(name))[1] = (select auth.uid())::text);
drop policy if exists documents_storage_update on storage.objects;
create policy documents_storage_update on storage.objects for update to authenticated
  using (bucket_id = 'documents' and (storage.foldername(name))[1] = (select auth.uid())::text)
  with check (bucket_id = 'documents' and (storage.foldername(name))[1] = (select auth.uid())::text);
drop policy if exists documents_storage_delete on storage.objects;
create policy documents_storage_delete on storage.objects for delete to authenticated
  using (bucket_id = 'documents' and (storage.foldername(name))[1] = (select auth.uid())::text);
