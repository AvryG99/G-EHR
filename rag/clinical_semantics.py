"""Clinical phrase normalization and feasible database value lookup."""

import math
import os
import re
from pathlib import Path

import numpy as np


CLINICAL_SYNONYMS = {
    "heart attack": "myocardial infarction",
    "high blood pressure": "hypertension",
    "low blood pressure": "hypotension",
    "kidney failure": "renal failure",
    "blood poisoning": "sepsis",
    "breathing machine": "mechanical ventilation",
}

LOOKUP_COLUMNS = {
    ("d_icd_diagnoses", "long_title"),
    ("d_icd_diagnoses", "short_title"),
    ("d_icd_procedures", "long_title"),
    ("d_labitems", "label"),
    ("d_items", "label"),
    ("prescriptions", "drug"),
}


def normalize_clinical_entities(question: str) -> str:
    """Expand common patient language into canonical clinical terminology."""
    normalized = question
    for phrase, clinical_term in CLINICAL_SYNONYMS.items():
        normalized = re.sub(
            rf"\b{re.escape(phrase)}\b",
            clinical_term,
            normalized,
            flags=re.IGNORECASE,
        )
    return normalized


class FeasibleValueLookup:
    """Rank real column values semantically, then by observed frequency."""

    def __init__(self, model, database_path: str | Path | None = None):
        self.model = model
        self.database_path = Path(
            database_path or os.getenv("MIMIC_LOCAL_DB", "mimic4.duckdb")
        )

    def get_feasible_column_values(
        self,
        table: str,
        column: str,
        query: str,
        limit: int = 5,
        candidate_limit: int = 500,
    ) -> list[dict]:
        if (table.lower(), column.lower()) not in LOOKUP_COLUMNS:
            raise ValueError(f"Lookup is not allowed for {table}.{column}")
        from executor.code_runner import RuntimeConfig, run_sql

        if RuntimeConfig.from_env().environment == "cloud":
            # Identifiers come exclusively from LOOKUP_COLUMNS above.
            table, column = table.lower(), column.lower()
            sql = (
                f"SELECT `{column}` AS value, COUNT(*) AS frequency "
                f"FROM `{table}` WHERE `{column}` IS NOT NULL "
                f"GROUP BY `{column}` ORDER BY frequency DESC LIMIT {int(candidate_limit)}"
            )
            result = run_sql(sql)
            if not result["success"]:
                raise RuntimeError(f"BigQuery value lookup failed: {result['error']}")
            candidates = [(row["value"], row["frequency"]) for row in result["rows"]]
        else:
            if not self.database_path.exists():
                return []
            import duckdb
            sql = (
                f'SELECT "{column}" AS value, COUNT(*) AS frequency '
                f'FROM "{table}" WHERE "{column}" IS NOT NULL '
                f'GROUP BY "{column}" ORDER BY frequency DESC LIMIT ?'
            )
            try:
                with duckdb.connect(str(self.database_path), read_only=True) as connection:
                    candidates = connection.execute(sql, [candidate_limit]).fetchall()
            except Exception:
                return []
        if not candidates:
            return []

        values = [str(value) for value, _ in candidates]
        embeddings = self.model.encode(values, normalize_embeddings=True)
        query_embedding = self.model.encode(query, normalize_embeddings=True)
        similarities = np.dot(embeddings, query_embedding)
        semantic_pool = sorted(
            zip(candidates, similarities),
            key=lambda item: float(item[1]),
            reverse=True,
        )[: max(limit * 4, limit)]
        semantic_pool.sort(key=lambda item: item[0][1], reverse=True)

        return [
            {
                "table": table,
                "column": column,
                "value": str(value),
                "frequency": int(frequency),
                "similarity": float(similarity),
            }
            for ((value, frequency), similarity) in semantic_pool[:limit]
            if math.isfinite(float(similarity))
        ]

    def lookup_for_rag(self, query: str, rag: dict, limit: int = 5) -> list[dict]:
        matches = []
        selected = {
            (table.lower(), column["name"].lower())
            for table, info in rag.get("tables_info", {}).items()
            for column in info.get("columns", [])
        }
        for table, column in sorted(selected & LOOKUP_COLUMNS):
            matches.extend(
                self.get_feasible_column_values(
                    table, column, query, limit=limit
                )
            )
        return matches
