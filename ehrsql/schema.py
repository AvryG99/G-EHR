"""Load the official Spider-style schema bundled with EHRSQL."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "ehrsql-ehragent"
DB_PATH = DATA_ROOT / "mimic_iii" / "mimic_iii.db"
VALID_PATH = DATA_ROOT / "mimic_iii" / "valid.json"
TRAIN_PATH = DATA_ROOT / "mimic_iii" / "train.json"
TABLES_PATH = DATA_ROOT / "tables.json"


@lru_cache(maxsize=1)
def load_schema() -> dict:
    schemas = json.loads(TABLES_PATH.read_text())
    return next(schema for schema in schemas if schema["db_id"] == "mimic_iii")


@lru_cache(maxsize=1)
def prompt_schema() -> dict:
    schema = load_schema()
    tables = {name.lower(): [] for name in schema["table_names_original"]}
    for index, ((table_index, name), column_type) in enumerate(
        zip(schema["column_names_original"], schema["column_types"])
    ):
        if table_index >= 0:
            table = schema["table_names_original"][table_index].lower()
            tables[table].append({"name": name.lower(), "type": column_type, "index": index})
    columns = schema["column_names_original"]
    foreign_keys = []
    for left, right in schema["foreign_keys"]:
        left_table, left_column = columns[left]
        right_table, right_column = columns[right]
        foreign_keys.append(
            f"{schema['table_names_original'][left_table].lower()}.{left_column.lower()} = "
            f"{schema['table_names_original'][right_table].lower()}.{right_column.lower()}"
        )
    return {
        "database": "EHRSQL cleaned MIMIC-III",
        "dialect": "SQLite",
        "fixed_current_time": "2105-12-31 23:59:00",
        "tables": {table: [{"name": c["name"], "type": c["type"]} for c in cols]
                   for table, cols in tables.items()},
        "foreign_keys": foreign_keys,
    }
