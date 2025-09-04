-- Supabase schema for Kaufland Fiyat Hesaplama App
-- Run this in Supabase Studio → SQL editor

-- UUID generation for primary keys
create extension if not exists pgcrypto;

-- Main table to store products
create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),

  -- Business columns (kept as text to match app’s current CSV/string format)
  title text,
  ean text,
  iwasku text,
  fiyat text,
  ham_maliyet_euro text,
  ham_maliyet_usd text,
  desi text,
  unit_in text,
  box_in text,
  pick_pack text,
  storage text,
  fedex text,
  tr_ne_navlun text,
  ne_de_navlun text,
  express_kargo text,
  ddp text,
  tr_de_navlun text,
  reklam text
);

-- Unique by EAN when present (ignore empty EANs)
create unique index if not exists products_ean_unique
  on public.products (ean)
  where ean is not null and ean <> '';

-- Enable Row Level Security
alter table public.products enable row level security;

-- Open RLS policies for anon (public) usage
-- Adjust if you need stricter rules or authenticated usage
-- Drop existing policies first (ignore errors if they don't exist)
drop policy if exists products_select on public.products;
drop policy if exists products_insert on public.products;
drop policy if exists products_update on public.products;
drop policy if exists products_delete on public.products;

-- Create new policies
create policy products_select on public.products
  for select using (true);

create policy products_insert on public.products
  for insert with check (true);

create policy products_update on public.products
  for update using (true);

create policy products_delete on public.products
  for delete using (true);

-- Optional: helpful index for title searches
create index if not exists products_title_idx on public.products (title);

-- Done
