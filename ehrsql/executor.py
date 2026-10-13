"""Read-only SQLite execution and official EHRSQL result normalization."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import sqlglot
from sqlglot import exp

from ehrsql.schema import DB_PATH


CURRENT_TIME = "2105-12-31 23:59:00"
VITAL_RANGES = {
    "temperature": (35.5, 38.1), "sao2": (95.0, 100.0),
    "heart rate": (60.0, 100.0), "respiration": (12.0, 18.0),
    "systolic bp": (90.0, 120.0), "diastolic bp": (60.0, 90.0),
    "mean bp": (60.0, 110.0),
}


def post_process_sql(query: str, current_time: str = CURRENT_TIME) -> str:
    """Match the official EHRSQL evaluator's deterministic substitutions."""
    query = query.lower()
    if "current_time" in query:
        query = query.replace("current_time", f"'{current_time}'")
    lower = re.search(r"[ \n]+([a-zA-Z0-9_]+_lower)", query)
    upper = re.search(r"[ \n]+([a-zA-Z0-9_]+_upper)", query)
    if lower and upper:
        names = set(re.findall(r"([a-zA-Z0-9_]+)_(?:lower|upper)", lower.group(1) + " " + upper.group(1)))
        if len(names) == 1:
            bounds = VITAL_RANGES.get(next(iter(names)).replace("_", " "))
            if bounds:
                query = query.replace(lower.group(1), str(bounds[0])).replace(upper.group(1), str(bounds[1]))
    return query.replace("''", "'").replace("< =", "<=").replace("%y", "%Y").replace("%j", "%J").replace("'now'", f"'{current_time}'")


def validate_read_only(sql: str) -> None:
    statements = sqlglot.parse(sql, read="sqlite")
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        raise ValueError("Exactly one read-only SELECT query is required")
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter)
    if any(statements[0].find(node) for node in forbidden):
        raise ValueError("Only read-only SELECT queries are allowed")


def execute(sql: str, db_path: Path = DB_PATH) -> list[tuple]:
    sql = post_process_sql(sql)
    validate_read_only(sql)
    uri = f"file:{db_path.resolve()}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=30) as connection:
        return connection.execute(sql).fetchall()


def official_answer(rows: list[tuple]) -> str:
    """Official metric: stringify, sort and compare up to the first 100 rows."""
    return str(sorted(str(row) for row in rows[:100]))


def run_sql(sql: str) -> dict:
    if sql.strip().lower() == "null":
        return {"success": True, "rows": [], "runtime": "ehrsql-local",
                "executed_sql": "null", "abstained": True}
    try:
        rows = execute(sql)
        return {"success": True, "rows": rows, "runtime": "ehrsql-local",
                "executed_sql": post_process_sql(sql), "abstained": False}
    except Exception as error:
        return {"success": False, "rows": [], "runtime": "ehrsql-local",
                "executed_sql": sql, "abstained": False, "error": str(error)}
