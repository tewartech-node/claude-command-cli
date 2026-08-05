"""Applies tables.sql and rpcs.sql to the existing Supabase project.

Two safety properties, both load-bearing given this project already has
live data and live callers:

1. Table statements use CREATE TABLE IF NOT EXISTS, so no existing table's
   columns are ever altered or dropped by this module — see tables.sql's
   header comment for the specific conflict this guards against.

2. `dry_run` defaults to True (config.MigrationSettings.dry_run). A dry
   run logs every statement it *would* execute and returns without
   calling Supabase at all. Set WARNETECH_MIGRATIONS_DRY_RUN=false (or
   pass dry_run=False explicitly) only after confirming rpcs.sql's
   `create or replace function` statements — unlike the tables, those DO
   overwrite live behavior; see rpcs.sql's header comment.
"""

from __future__ import annotations

from pathlib import Path

from .config import SchemaConfig, DEFAULT_CONFIG
from .logging import get_logger, log_migration_step
from .utils import SqlExecutionError, execute_sql_with_retry, split_statements

logger = get_logger(__name__)

_SCHEMA_DIR = Path(__file__).resolve().parent


class MigrationError(Exception):
    pass


def _read_sql(filename: str) -> str:
    path = _SCHEMA_DIR / filename
    if not path.exists():
        raise MigrationError(f"{filename} not found at {path}")
    return path.read_text(encoding="utf-8")


def apply_file(config: SchemaConfig, filename: str, dry_run: bool | None = None) -> dict:
    dry_run = config.migration.dry_run if dry_run is None else dry_run
    sql_text = _read_sql(filename)
    statements = split_statements(sql_text)

    log_migration_step(logger, f"apply_{filename}", "started", {"statement_count": len(statements), "dry_run": dry_run})

    applied = 0
    errors: list[dict] = []

    for i, statement in enumerate(statements):
        step_name = f"{filename}[{i}]"
        if dry_run:
            log_migration_step(logger, step_name, "dry_run", {"preview": statement[:200]})
            applied += 1
            continue

        try:
            execute_sql_with_retry(config, statement)
            log_migration_step(logger, step_name, "applied")
            applied += 1
        except SqlExecutionError as exc:
            log_migration_step(logger, step_name, "failed", {"error": str(exc), "status": exc.status})
            errors.append({"statement_index": i, "error": str(exc), "status": exc.status})

    result = {
        "file": filename,
        "dry_run": dry_run,
        "total_statements": len(statements),
        "applied": applied,
        "errors": errors,
    }
    log_migration_step(logger, f"apply_{filename}", "completed" if not errors else "completed_with_errors", result)
    return result


def apply_schema(config: SchemaConfig = DEFAULT_CONFIG, dry_run: bool | None = None) -> dict:
    """Applies tables.sql then rpcs.sql, in that order — RPCs reference
    tables (metric_rollups, anomalies) that must already exist.
    """
    tables_result = apply_file(config, config.migration.tables_file, dry_run)
    rpcs_result = apply_file(config, config.migration.rpcs_file, dry_run)

    return {
        "tables": tables_result,
        "rpcs": rpcs_result,
        "ok": not tables_result["errors"] and not rpcs_result["errors"],
    }


def main() -> int:
    result = apply_schema()
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
