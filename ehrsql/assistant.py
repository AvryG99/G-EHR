"""SQL-only assistant for the cleaned EHRSQL MIMIC-III database."""
from __future__ import annotations

import json
import re
from functools import lru_cache

from ehrsql.executor import run_sql
from ehrsql.schema import TRAIN_PATH, prompt_schema


TOKEN = re.compile(r"[a-z0-9]+")


def extract_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.I | re.S)
    return (match.group(1) if match else text).strip().rstrip(";")


@lru_cache(maxsize=1)
def training_examples() -> list[dict]:
    return json.loads(TRAIN_PATH.read_text())


def retrieve_examples(question: str, count: int = 4) -> list[dict]:
    query_tokens = set(TOKEN.findall(question.lower()))
    scored = []
    for index, example in enumerate(training_examples()):
        tokens = set(TOKEN.findall(example["question"].lower()))
        overlap = len(query_tokens & tokens) / max(1, len(query_tokens | tokens))
        scored.append((overlap, -index, example))
    return [item[2] for item in sorted(scored, reverse=True)[:count]]


class EHRSQLAssistant:
    def __init__(self, llm, max_retry: int = 3, max_fewshot: int = 4, retriever=None):
        self.llm = llm
        self.max_retry = max_retry
        self.max_fewshot = max_fewshot
        self.schema = prompt_schema()
        self.retriever = retriever

    def build_prompt(self, question: str) -> str:
        schema = self.retriever.retrieve(question) if self.retriever else self.schema
        retrieved = (self.retriever.retrieve_examples(question, self.max_fewshot)
                     if self.retriever else retrieve_examples(question, self.max_fewshot))
        examples = [{"question": ex["question"], "sql": ex["query"]} for ex in retrieved]
        return f"""Generate one SQLite query for the cleaned EHRSQL MIMIC-III benchmark.
Return SQL only. If the question cannot be answered from the supplied schema,
return exactly null. Do not use knowledge of the original MIMIC-III schema.

Rules:
- Use only listed tables and columns. This cleaned database intentionally has
  admissions.age, cost, and charttime on diagnoses_icd/procedures_icd.
- current_time means 2105-12-31 23:59:00. Use SQLite date/datetime/strftime.
- Preserve values and identifiers from the question exactly.
- Use declared foreign keys. Avoid row_id joins unless explicitly declared.
- Never invent a table or column. Do not output prose or Markdown.

Schema JSON:
{json.dumps(schema, separators=(',', ':'))}

Training examples JSON:
{json.dumps(examples, separators=(',', ':'))}

Question:
{question}

SQL:"""

    def query(self, question: str) -> tuple[str, dict]:
        prompt = self.build_prompt(question)
        last_sql = "null"
        last_result = {"success": False, "error": "No attempt made", "rows": []}
        for attempt in range(self.max_retry + 1):
            if attempt:
                prompt = f"""The SQLite query failed. Repair it without changing intent.
Use only this allowed schema. Return SQL only, or exactly null if unanswerable.
Question: {question}
Failed SQL: {last_sql}
SQLite error: {last_result.get('error')}
Schema JSON: {json.dumps(self.schema, separators=(',', ':'))}
SQL:"""
            last_sql = extract_sql(self.llm.generate(prompt))
            last_result = run_sql(last_sql)
            if last_result["success"]:
                return last_sql, last_result
        return last_sql, last_result
