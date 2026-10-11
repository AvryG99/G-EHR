import json
from datetime import datetime


def log_repair_prompt(
    path: str,
    attempt: int,
    sql_before: str,
    error: dict,
    schema_info: dict,
    prompt: str,
    sql_after: str | None = None
):
    with open(path, "a", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write(f"TIMESTAMP : {datetime.now().isoformat()}\n")
        f.write(f"ATTEMPT   : {attempt}\n\n")

        f.write("SQL_BEFORE:\n")
        f.write(sql_before.strip() + "\n\n")

        f.write("DB_ERROR:\n")
        f.write(json.dumps(error, indent=2, ensure_ascii=False) + "\n\n")

        f.write("SCHEMA_INFO:\n")
        f.write(json.dumps(schema_info, indent=2, ensure_ascii=False) + "\n\n")

        f.write("REPAIR_PROMPT:\n")
        f.write(prompt.strip() + "\n\n")

        if sql_after:
            f.write("SQL_AFTER:\n")
            f.write(sql_after.strip() + "\n\n")
