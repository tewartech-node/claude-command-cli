-- supabase_schema/rpcs.sql
--
-- APPLIED 2026-08-05 against tewartech-project-supabase (dcepcfnnqiwccbnnsdcq),
-- per explicit approval of exactly this behavior change (unlike tables.sql,
-- this file's CREATE OR REPLACE FUNCTION statements are not a no-op — they
-- actually replaced the live functions). The versions below are narrower
-- than what was live before this migration:
--
--   maintain_partitions() previously also created ahead-partitions for
--   threat_events, not only metric_rollups. Applying this file stopped
--   that — threat_events partition maintenance is no longer covered by
--   this RPC. Existing threat_events partitions are unaffected (already
--   created through October 2026), but nothing will extend that coverage
--   further ahead unless threat_events support is added back here.
--
--   refresh_metric_rollups() below additionally summarizes anomalies,
--   which the previous live version did not. Verified live: returns
--   {"metrics": {...}, "anomalies": {"total_rows": N, "by_severity": {...}}}.
--
-- migrations.py still defaults to a dry run for any future re-application
-- (e.g. against a different project) — this header records that this
-- specific approval and application already happened here.

create or replace function public.maintain_partitions()
returns jsonb
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_table text := 'metric_rollups';
  v_month date;
  v_partition_name text;
  v_start timestamptz;
  v_end timestamptz;
  v_created text[] := '{}';
  i integer;
begin
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

  return jsonb_build_object('created_partitions', to_jsonb(v_created), 'checked_at', now());
end;
$function$;

create or replace function public.refresh_metric_rollups()
returns jsonb
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_metric_total bigint;
  v_metric_by_partition jsonb;
  v_anomaly_total bigint;
  v_anomaly_by_severity jsonb;
begin
  select count(*) into v_metric_total from public.metric_rollups;
  select coalesce(jsonb_object_agg(relname, cnt), '{}'::jsonb) into v_metric_by_partition
  from (
    select c.relname, count(*) as cnt
    from public.metric_rollups m
    join pg_class c on c.oid = m.tableoid
    group by c.relname
  ) t;

  select count(*) into v_anomaly_total from public.anomalies;
  select coalesce(jsonb_object_agg(severity, cnt), '{}'::jsonb) into v_anomaly_by_severity
  from (
    select severity, count(*) as cnt
    from public.anomalies
    group by severity
  ) a;

  return jsonb_build_object(
    'metrics', jsonb_build_object('total_rows', v_metric_total, 'by_partition', v_metric_by_partition),
    'anomalies', jsonb_build_object('total_rows', v_anomaly_total, 'by_severity', v_anomaly_by_severity),
    'refreshed_at', now()
  );
end;
$function$;
