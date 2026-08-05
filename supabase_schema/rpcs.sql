-- supabase_schema/rpcs.sql
--
-- These are the ORIGINAL maintain_partitions() and refresh_metric_rollups()
-- definitions, as first created against tewartech-project-supabase
-- (dcepcfnnqiwccbnnsdcq) earlier in this project's history. A narrower
-- alternative (metric_rollups-only maintenance; anomalies added to the
-- refresh summary) was briefly applied live on 2026-08-05 and then
-- reverted the same day back to this original version — this file reflects
-- what is actually live now, not the narrower alternative.
--
-- maintain_partitions() covers BOTH metric_rollups and threat_events: it
-- ensures the current + next 2 months' partitions exist for each,
-- complementing drop_old_partitions() (which quota_watchdog() already
-- calls for the trailing edge).
--
-- refresh_metric_rollups() reports current metric_rollups row counts by
-- partition. It does not summarize anomalies — raw samples for metrics
-- live in the D1 edge buffer and R2 archives, not in Postgres, so this is
-- an honest summary of what has already been written here, not a
-- recomputation from source data that isn't present in this database.

create or replace function public.maintain_partitions()
returns jsonb
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_table text;
  v_month date;
  v_partition_name text;
  v_start timestamptz;
  v_end timestamptz;
  v_created text[] := '{}';
  i integer;
begin
  foreach v_table in array array['metric_rollups', 'threat_events']
  loop
    for i in 0..2 loop
      v_month := (date_trunc('month', now()) + (i || ' months')::interval)::date;
      v_partition_name := v_table || '_' || to_char(v_month, 'YYYYMM');
      v_start := v_month;
      v_end := v_month + interval '1 month';

      if not exists (select 1 from pg_class where relname = v_partition_name) then
        execute format(
          'create table if not exists public.%I partition of public.%I for values from (%L) to (%L)',
          v_partition_name, v_table, v_start, v_end
        );
        v_created := v_created || v_partition_name;
      end if;
    end loop;
  end loop;

  return jsonb_build_object('created_partitions', to_jsonb(v_created), 'checked_at', now());
end;
$function$;

create or replace function public.refresh_metric_rollups()
returns jsonb
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_total bigint;
  v_by_partition jsonb;
begin
  select count(*) into v_total from public.metric_rollups;

  select coalesce(jsonb_object_agg(relname, cnt), '{}'::jsonb) into v_by_partition
  from (
    select c.relname, count(*) as cnt
    from public.metric_rollups m
    join pg_class c on c.oid = m.tableoid
    group by c.relname
  ) t;

  return jsonb_build_object(
    'total_rows', v_total,
    'by_partition', v_by_partition,
    'refreshed_at', now()
  );
end;
$function$;
