-- supabase_schema/rpcs.sql
--
-- IMPORTANT: maintain_partitions() and refresh_metric_rollups() already
-- exist live (see docs' WARNETECH-CANONICAL-WIRING-SPEC.txt task history).
-- Unlike tables.sql's CREATE TABLE IF NOT EXISTS, `create or replace
-- function` here WOULD overwrite the live functions' actual behavior, not
-- just no-op — the versions below are narrower than what is live today:
--
--   maintain_partitions() currently also creates ahead-partitions for
--   threat_events, not only metric_rollups. Replacing it with the version
--   below would silently stop threat_events partition maintenance.
--
--   refresh_metric_rollups() below additionally summarizes anomalies,
--   which the live version does not.
--
-- migrations.py defaults to a dry run specifically because of this file;
-- do not apply it for real until this behavior change is confirmed.

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
