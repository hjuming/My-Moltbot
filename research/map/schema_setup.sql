-- 1. Enable PostGIS extension for Geospatial queries
create extension if not exists postgis;

-- 2. Create the main 'places' table
create table public.places (
  id uuid default gen_random_uuid() primary key,
  
  -- Basic Info
  name text not null,
  original_name text, -- For deduplication
  
  -- Classification
  category text not null, -- food, dive, pet, travel
  subcategory text,       -- cafe, shore_dive, hotel...
  
  -- Strategy Strategy (The 3 Types)
  dataset_type text check (dataset_type in ('google_ref', 'proprietary', 'enriched')),
  
  -- Location (PostGIS Point)
  location geography(POINT, 4326),
  address text,
  
  -- For Type A (Reference)
  google_place_id text unique,
  google_url text,
  
  -- Flexible Metadata (For Type B & C specific fields)
  metadata jsonb default '{}'::jsonb,
  
  -- Status & Maintenance
  rating numeric(3, 1),
  is_verified boolean default false,
  is_closed boolean default false,
  updated_at timestamp with time zone default now(),
  created_at timestamp with time zone default now()
);

-- 3. Create a spatial index for fast location search (e.g. Find diving spots within 5km)
create index places_location_idx on public.places using GIST (location);

-- 4. Enable Row Level Security (RLS)
alter table public.places enable row level security;

-- 5. Policies
-- Policy: Everyone can READ (Public API)
create policy "Public places are viewable by everyone" 
on public.places for select 
using (true);

-- Policy: Only Service Role (our Scripts) can INSERT/UPDATE/DELETE
-- (No anon/authenticated user can modify data directly)
create policy "Service role can modify places"
on public.places for all
using (auth.role() = 'service_role');
