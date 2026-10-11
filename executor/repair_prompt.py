import json


def build_repair_prompt(sql: str, error: dict, schema_info: dict) -> str:
    return f"""
The following SQL query failed.

SQL:
{sql}

Database error:
{json.dumps(error, indent=2)}

Relevant schema (STRICT):
{json.dumps(schema_info, indent=2)}

TASK:
- Fix the SQL query
- DO NOT change intent
- Use ONLY provided tables/columns
- Google BigQuery Standard SQL syntax only
- Output ONLY SQL
"""
