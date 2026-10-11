"""Shared core workflow for the MIMIC-IV database assistant."""

import json
import re
from decimal import Decimal
from typing import Any, Sequence

from langchain_core.messages import AIMessage, HumanMessage

from executor.code_runner import run_sql
from executor.error_parser import parse_sql_error
from executor.repair_prompt import build_repair_prompt
from executor.schema_utils import get_columns_like, get_table_schema, get_tables_like
from rag.clinical_semantics import normalize_clinical_entities


def json_safe(value: Any) -> Any:
    """Recursively convert database values into JSON-serializable values."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def extract_sql(text: str) -> str:
    """Extract SQL from a fenced model response, or return plain text."""
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def extract_tables_from_sql(sql: str) -> list[str]:
    try:
        import sqlglot
        from sqlglot import exp

        expression = sqlglot.parse_one(sql, read="bigquery")
        return sorted({table.name for table in expression.find_all(exp.Table)})
    except (ImportError, ValueError):
        pass

    patterns = (
        r"FROM\s+(\w+)",
        r"JOIN\s+(\w+)",
        r"INTO\s+(\w+)",
        r"UPDATE\s+(\w+)",
    )
    tables = {
        match.group(1)
        for pattern in patterns
        for match in re.finditer(pattern, sql, re.IGNORECASE)
    }
    return sorted(tables)


def get_relevant_schemas(sql: str) -> dict[str, list[dict[str, Any]]]:
    schemas = {}
    for table in extract_tables_from_sql(sql):
        columns = get_table_schema(table)
        if columns:
            schemas[table] = [
                {
                    "column_name": column["column_name"],
                    "data_type": column["data_type"],
                }
                for column in columns
            ]
    return schemas


def build_schema_context_for_repair(error_info: dict, sql: str) -> dict:
    schema_info = {"existing_tables": get_relevant_schemas(sql)}

    if error_info["type"] == "unknown_table":
        schema_info["suggested_tables"] = get_tables_like(error_info["name"])[:5]
    elif error_info["type"] == "unknown_column":
        schema_info["suggested_columns"] = [
            {"table": column["table_name"], "column": column["column_name"]}
            for column in get_columns_like(error_info["name"])[:5]
        ]

    return schema_info


class MedicalDatabaseAssistant:
    """Coordinate conversation resolution, retrieval, SQL, and final answers."""

    def __init__(
        self,
        llm,
        retriever,
        fewshot_retriever,
        value_lookup=None,
        max_fewshot=3,
        max_retry=3,
    ):
        self.llm = llm
        self.retriever = retriever
        self.fewshot_retriever = fewshot_retriever
        self.value_lookup = value_lookup
        self.max_fewshot = max_fewshot
        self.max_retry = max_retry

    def resolve_question_with_context(
        self, question: str, chat_history: Sequence
    ) -> str:
        if not chat_history:
            return question

        context = []
        for message in chat_history[-6:]:
            if isinstance(message, HumanMessage):
                context.append(f"User: {message.content}")
            elif isinstance(message, AIMessage):
                context.append(f"Assistant: {message.content}")

        prompt = f"""
Resolve pronouns or references in the new question using the conversation history.

Conversation:
{chr(10).join(context)}

Question:
{question}

Return the resolved question:
"""
        try:
            return self.llm.generate(prompt)
        except Exception:
            return question

    def build_prompt(
        self, question, rag, resolved_question=None, feasible_values=None
    ):
        q = resolved_question or question

        fewshots = self.fewshot_retriever.retrieve(q, self.max_fewshot)
        fewshot_text = ""
        for ex in fewshots:
            fewshot_text += f"""
Example:
Question: {ex['question']}
SQL:
{ex['sql']}
"""

        schema_text = ""
        for table, info in rag["tables_info"].items():
            schema_text += f"\n## {table}\n"
            for col in info["columns"]:
                schema_text += f"- {col['name']}: {col['description'][:150]}\n"

        join_text = json.dumps(rag.get("join_paths", []), ensure_ascii=False)
        value_text = json.dumps(feasible_values or [], ensure_ascii=False)

        return f"""
You are an expert medical SQL analyst.

{fewshot_text}

Question:
{q}

Allowed schema:
{schema_text}

Valid join paths:
{join_text}

Feasible clinical values and codes:
{value_text}

Rules:
- Use only given schema
- Google BigQuery Standard SQL syntax
- Use only the valid join paths and keys provided
- Constrain chartevents and labevents with an itemid from the lookup values
- Output SQL only

Write SQL:
"""

    def generate_sql_with_retry(
        self,
        question,
        rag,
        resolved_question=None,
        feasible_values=None,
    ):
        sql = None
        last_error = None

        for attempt in range(self.max_retry + 1):
            if attempt == 0:
                prompt = self.build_prompt(
                    question, rag, resolved_question, feasible_values
                )
            else:
                error_info = parse_sql_error(last_error)
                prompt = build_repair_prompt(
                    sql,
                    error_info,
                    build_schema_context_for_repair(error_info, sql),
                )

            sql = extract_sql(self.llm.generate(prompt))
            result = run_sql(sql)
            if result["success"]:
                return sql, result

            last_error = result["error"]

        return sql, {"success": False, "error": last_error}

    def generate_natural_response(self, question, result, success):
        if not success:
            return "I encountered an error while processing your question."

        rows = result.get("rows", [])
        if not rows:
            result_text = "No data found."
        elif len(rows) == 1:
            result_text = json.dumps(json_safe(rows[0]), ensure_ascii=False)
        else:
            result_text = json.dumps(
                json_safe(rows[:10]), ensure_ascii=False, indent=2
            )

        prompt = f"""
You are a medical data assistant.

Question:
{question}

Result:
{result_text}

Answer concisely in English without mentioning SQL.
"""
        return self.llm.generate(prompt)

    def answer(self, question: str, chat_history: Sequence):
        """Answer one question and return the answer plus execution details."""
        resolved = self.resolve_question_with_context(question, chat_history)
        normalized = normalize_clinical_entities(resolved)
        rag = self.retriever.rag_retrieve(normalized)
        feasible_values = (
            self.value_lookup.lookup_for_rag(normalized, rag)
            if self.value_lookup
            else []
        )
        sql, result = self.generate_sql_with_retry(
            question, rag, normalized, feasible_values
        )
        answer = self.generate_natural_response(
            question, result, result["success"]
        )
        return answer, sql, result
