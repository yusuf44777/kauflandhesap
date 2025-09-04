-- Mevcut tabloyu kaldır ve yeniden oluştur
-- Bu script'i Supabase Dashboard > SQL Editor'de çalıştırın

-- Mevcut tabloyu sil
DROP TABLE IF EXISTS public.products CASCADE;

-- UUID generation for primary keys
create extension if not exists pgcrypto;

-- Main table to store products
create table public.products (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),

  -- Business columns (kept as text to match app's current CSV/string format)
  title text,
  ean text,
  iwasku text,
  fiyat text,
  ham_maliyet_euro text,
  desi text,
  tr_ne_navlun text,
  ne_de_navlun text,
  kara_tr_de_navlun text,
  express_kargo text,
  ddp text,
  hava_tr_de_navlun text,
  reklam text
);

-- Unique by EAN when present (ignore empty EANs)
create unique index products_ean_unique
  on public.products (ean)
  where ean is not null and ean <> '';

-- Enable Row Level Security
alter table public.products enable row level security;

-- Open RLS policies for anon (public) usage
-- Adjust if you need stricter rules or authenticated usage
create policy products_select on public.products
  for select using (true);

create policy products_insert on public.products
  for insert with check (true);

create policy products_update on public.products
  for update using (true);

create policy products_delete on public.products
  for delete using (true);

-- Optional: helpful index for title searches
create index products_title_idx on public.products (title);

-- Kontrol sorgusu
SELECT 'Tablo başarıyla oluşturuldu!' as message;
