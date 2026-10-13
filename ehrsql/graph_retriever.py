"""Schema Graph-RAG for the cleaned EHRSQL MIMIC-III schema."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re

import networkx as nx
import numpy as np
from sentence_transformers import SentenceTransformer

from ehrsql.schema import TRAIN_PATH, prompt_schema
from graph.des import TABLE_DESCRIPTIONS


class EHRSQLGraphRetriever:
    """Dense column retrieval followed by foreign-key graph expansion."""

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5", top_k: int = 30,
                 max_seed_tables: int = 6):
        self.schema = prompt_schema()
        self.top_k = top_k
        self.max_seed_tables = max_seed_tables
        self.model = SentenceTransformer(model_name, device="cpu", local_files_only=True)
        self.documents = []
        self.entries = []
        for table, columns in self.schema["tables"].items():
            description = TABLE_DESCRIPTIONS.get(table, table.replace("_", " "))
            for column in columns:
                self.entries.append((table, column["name"]))
                self.documents.append(
                    f"table {table}; column {column['name']}; type {column['type']}; {description}"
                )
        embeddings = self.model.encode(self.documents, convert_to_numpy=True,
                                       normalize_embeddings=True, show_progress_bar=False)
        self.embeddings = np.asarray(embeddings, dtype="float32")
        self.training = json.loads(TRAIN_PATH.read_text())
        cache = Path(__file__).with_name("ehrsql_train_embeddings.npy")
        if cache.exists():
            self.training_embeddings = np.load(cache)
        else:
            self.training_embeddings = np.asarray(self.model.encode(
                [row["question"] for row in self.training], batch_size=64,
                convert_to_numpy=True, normalize_embeddings=True,
                show_progress_bar=True), dtype="float32")
            np.save(cache, self.training_embeddings)
        self.graph = nx.Graph()
        self.graph.add_nodes_from(self.schema["tables"])
        for relation in self.schema["foreign_keys"]:
            left, right = relation.split(" = ")
            self.graph.add_edge(left.split(".")[0], right.split(".")[0], relation=relation)

    def retrieve(self, question: str) -> dict:
        query = self.model.encode([question], convert_to_numpy=True,
                                  normalize_embeddings=True, show_progress_bar=False)[0]
        scores = self.embeddings @ query
        indexes = np.argsort(scores)[::-1][:self.top_k]
        table_scores = defaultdict(float)
        matched_columns = defaultdict(list)
        lowered = question.lower()
        for index in indexes:
            table, column = self.entries[int(index)]
            score = float(scores[int(index)])
            if table in lowered or table.replace("_", " ") in lowered:
                score += .35
            if column in lowered or column.replace("_", " ") in lowered:
                score += .25
            table_scores[table] += max(0.0, score)
            matched_columns[table].append({"name": column, "score": round(score, 4)})
        seeds = [table for table, _ in sorted(table_scores.items(), key=lambda x: (-x[1], x[0]))
                 [:self.max_seed_tables]]
        selected = set(seeds)
        for i, left in enumerate(seeds):
            for right in seeds[i + 1:]:
                try:
                    selected.update(nx.shortest_path(self.graph, left, right))
                except nx.NetworkXNoPath:
                    pass
        foreign_keys = [fk for fk in self.schema["foreign_keys"]
                        if all(part.split(".")[0] in selected for part in fk.split(" = "))]
        return {
            "database": self.schema["database"], "dialect": self.schema["dialect"],
            "fixed_current_time": self.schema["fixed_current_time"],
            "retrieved_tables": seeds, "graph_expanded_tables": sorted(selected),
            "matched_columns": {table: matched_columns[table] for table in seeds},
            "tables": {table: self.schema["tables"][table] for table in sorted(selected)},
            "foreign_keys": foreign_keys,
        }

    def retrieve_examples(self, question: str, count: int = 4) -> list[dict]:
        query = self.model.encode([question], convert_to_numpy=True,
                                  normalize_embeddings=True, show_progress_bar=False)[0]
        indexes = np.argsort(self.training_embeddings @ query)[::-1][:count]
        return [self.training[int(index)] for index in indexes]
