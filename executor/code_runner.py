"""Cost-safe execution for GoogleSQL against local DuckDB or BigQuery."""

import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


HIGH_VOLUME_TABLES = {"chartevents", "labevents"}


@dataclass(frozen=True)
class RuntimeConfig:
    environment: Literal["local", "cloud"]
    local_database: Path
    bigquery_project: str | None
    bigquery_dataset: str | None
    maximum_bytes_billed: int

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        environment = os.getenv("MIMIC_ENV", "local").lower()
        if environment not in {"local", "cloud"}:
            raise ValueError("MIMIC_ENV must be either 'local' or 'cloud'")
        return cls(
            environment=environment,
            local_database=Path(os.getenv("MIMIC_LOCAL_DB", "mimic4.duckdb")),
            bigquery_project=os.getenv("BIGQUERY_PROJECT"),
            bigquery_dataset=os.getenv("BIGQUERY_DATASET"),
            maximum_bytes_billed=int(
                os.getenv("BIGQUERY_MAXIMUM_BYTES_BILLED", "1000000000")
            ),
        )


def transpile_for_duckdb(sql: str) -> str:
    """Translate Google BigQuery Standard SQL to DuckDB SQL."""
    import sqlglot

    statements = sqlglot.transpile(sql, read="bigquery", write="duckdb")
    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is required")
    return statements[0]


def validate_scan_guards(sql: str) -> None:
    """Reject unbounded scans of the largest clinical event tables."""
    import sqlglot
    from sqlglot import exp

    expression = sqlglot.parse_one(sql, read="bigquery")
    referenced = {table.name.lower() for table in expression.find_all(exp.Table)}
    guarded = referenced & HIGH_VOLUME_TABLES
    if not guarded:
        return

    where = expression.find(exp.Where)
    itemid_is_constrained = bool(where) and any(
        any(
            column.name.lower() == "itemid"
            for column in predicate.find_all(exp.Column)
        )
        for predicate in where.find_all(exp.EQ, exp.In, exp.Between)
    )
    if not itemid_is_constrained:
        names = ", ".join(sorted(guarded))
        raise ValueError(
            f"High-volume table(s) {names} require an itemid constraint "
            "resolved through a lookup table/value."
        )


def _rows_as_dicts(cursor) -> list[dict]:
    columns = [description[0] for description in cursor.description or ()]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _run_local(sql: str, config: RuntimeConfig) -> dict:
    import duckdb

    duckdb_sql = transpile_for_duckdb(sql)
    with duckdb.connect(str(config.local_database), read_only=True) as connection:
        cursor = connection.execute(duckdb_sql)
        rows = _rows_as_dicts(cursor)
    return {
        "success": True,
        "rows": rows,
        "runtime": "local",
        "executed_sql": duckdb_sql,
    }


def _run_cloud(sql: str, config: RuntimeConfig) -> dict:
    if not config.bigquery_project or not config.bigquery_dataset:
        raise RuntimeError(
            "BIGQUERY_PROJECT and BIGQUERY_DATASET are required in cloud mode"
        )

    from google.cloud import bigquery

    client = bigquery.Client(project=config.bigquery_project)
    dry_run_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry_run = client.query(sql, job_config=dry_run_config)
    estimated_bytes = dry_run.total_bytes_processed
    if estimated_bytes > config.maximum_bytes_billed:
        raise RuntimeError(
            f"Query would process {estimated_bytes} bytes, exceeding the "
            f"configured limit of {config.maximum_bytes_billed} bytes"
        )

    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{config.bigquery_project}.{config.bigquery_dataset}",
        maximum_bytes_billed=config.maximum_bytes_billed,
        use_query_cache=True,
    )
    rows = [dict(row.items()) for row in client.query(sql, job_config=job_config)]
    return {
        "success": True,
        "rows": rows,
        "runtime": "cloud",
        "estimated_bytes": estimated_bytes,
        "executed_sql": sql,
    }


def run_sql(sql: str, params=None, config: RuntimeConfig | None = None):
    """Validate GoogleSQL locally, then optionally execute it on BigQuery."""
    del params
    config = config or RuntimeConfig.from_env()
    try:
        validate_scan_guards(sql)
        local_result = _run_local(sql, config)
        if config.environment == "local":
            return local_result

        cloud_result = _run_cloud(sql, config)
        cloud_result["sandbox_sql"] = local_result["executed_sql"]
        return cloud_result
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "runtime": config.environment,
        }
