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


def log_sql_prompt(prompt: str, question: str, attempt: int, stage=None) -> None:
    """Append the exact SQL-generation prompt before calling the model."""
    import os
    from pathlib import Path
    from zoneinfo import ZoneInfo

    project_root = Path(__file__).resolve().parents[1]
    path = Path(os.getenv('MIMIC_PROMPT_LOG', 'logs/sql_prompts.jsonl'))
    if not path.is_absolute():
        path = project_root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        'timestamp': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),
        'stage': stage or ('sql_generation' if attempt == 0 else 'sql_repair'),
        'attempt': attempt,
        'question': question,
        'prompt': prompt,
    }
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    if os.getenv('MIMIC_DEBUG', '0').lower() in {'1', 'true'}:
        print(f'\nGenerated SQL prompt (attempt {attempt}):\n{prompt}')
