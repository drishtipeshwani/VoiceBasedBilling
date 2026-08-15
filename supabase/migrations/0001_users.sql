-- Run this in the Supabase SQL editor (Dashboard > SQL Editor) for your project.
-- Creates a `users` table that stores each user's name and company name,
-- keyed to Supabase's built-in `auth.users` table.
-- Note: this lives in the `public` schema (public.users), which is distinct
-- from Supabase's own `auth.users` table (auth schema) -- no name collision,
-- but worth keeping the schema distinction in mind when querying.

create table if not exists public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  name text,
  company_name text,
  created_at timestamptz not null default now()
);

alter table public.users enable row level security;

create policy "Users can view their own row"
  on public.users
  for select
  using (auth.uid() = id);

create policy "Users can update their own row"
  on public.users
  for update
  using (auth.uid() = id);

create policy "Users can insert their own row"
  on public.users
  for insert
  with check (auth.uid() = id);

-- Automatically creates a `users` row whenever a new auth user signs up.
-- `name` / `company_name` come from the `options.data` passed to
-- `supabase.auth.signUp()` on the client (see utils/authContext.tsx),
-- which Supabase stores as `raw_user_meta_data` on the auth.users row.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.users (id, name, company_name)
  values (
    new.id,
    new.raw_user_meta_data ->> 'name',
    new.raw_user_meta_data ->> 'company_name'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();

--- Every table has a primary key
-- Multiple tables are reference each other using a Foreign Key relationship 
-- A referenced key is always a column of set of columns that have UNIQUE constraint and that we feel will not change over time 
create table if not exists public.stock (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  name text not null,
  quantity integer not null default 0,
  purchase_price numeric(12, 2) not null default 0,
  selling_price numeric(12, 2) not null default 0,
  created_at timestamptz not null default now()
);

alter table public.stock enable row level security;

create policy "Users can view their own stock"
  on public.stock
  for select
  using (auth.uid() = user_id);

create policy "Users can insert their own stock"
  on public.stock
  for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own stock"
  on public.stock
  for update
  using (auth.uid() = user_id);

create policy "Users can delete their own stock"
  on public.stock
  for delete
  using (auth.uid() = user_id);

create table if not exists public.customers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now()
);

alter table public.customers enable row level security;

create policy "Users can view their own customers"
  on public.customers
  for select
  using (auth.uid() = user_id);

create policy "Users can insert their own customers"
  on public.customers
  for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own customers"
  on public.customers
  for update
  using (auth.uid() = user_id);

create policy "Users can delete their own customers"
  on public.customers
  for delete
  using (auth.uid() = user_id);
