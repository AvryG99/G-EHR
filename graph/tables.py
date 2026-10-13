"""Original MIMIC-III schema from MIT SchemaSpy (26 logical tables).

Physical chartevents partitions are excluded; query chartevents instead.
Source: https://lcp.mit.edu/mimic-schema-spy/
"""
import json
from pathlib import Path

tables = json.loads(Path(__file__).with_name("mimiciii_schema.json").read_text())


def unique_columns():
    """Derive retrieval metadata from the same schema used by the graph."""
    columns = {}
    for table, info in tables.items():
        for name, attribute in info["attributes"].items():
            column = columns.setdefault(name, {"description": "", "tables": []})
            column["tables"].append(table)
            column["description"] += f" {table}.{name}: {attribute['description']} ({attribute['datatype']})."
    return columns
