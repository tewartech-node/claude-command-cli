-- supabase_schema/tables.sql
--
-- IMPORTANT: test_results, ai_decisions, and security_events already exist
-- in the live project (tewartech-project-supabase / dcepcfnnqiwccbnnsdcq),
-- created by an earlier migration with a DIFFERENT column set than what
-- follows here (bigint identity ids, not uuid; different column names).
-- CREATE TABLE IF NOT EXISTS is used throughout specifically so this file
-- is safe to run against that project: it will silently do nothing for
-- these three tables rather than error or touch existing data. It matches
-- the requested schema exactly only against a project where these tables
-- do not yet exist. See migrations.py's module docstring for the
-- reconciliation options.

create extension if not exists pgcrypto;

create table if not exists public.test_results (
  id uuid primary key default gen_random_uuid(),
  scenario text,
  status text,
  details jsonb,
  metrics jsonb,
  anomalies jsonb,
  created_at timestamptz default now()
);

create table if not exists public.ai_decisions (
  id uuid primary key default gen_random_uuid(),
  decision_type text,
  input jsonb,
  output jsonb,
  confidence numeric,
  created_at timestamptz default now()
);

create table if not exists public.security_events (
  id uuid primary key default gen_random_uuid(),
  event_type text,
  source text,
  details jsonb,
  severity text,
  created_at timestamptz default now()
);

alter table public.test_results enable row level security;
alter table public.ai_decisions enable row level security;
alter table public.security_events enable row level security;
