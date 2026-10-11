import json
import os
import faiss
import numpy as np
import networkx as nx
from collections import Counter, defaultdict
from typing import List, Dict

from sentence_transformers import SentenceTransformer

from graph.graph_builder import build_schema_graph, describe_join_paths

# Query Expansion (rule-based)

QUERY_EXPANSIONS = {
    'medication': ['drug', 'prescription', 'treatment', 'therapy'],
    'drug': ['medication', 'prescription', 'pharmaceutical'],
    'test': ['lab', 'examination', 'investigation', 'analysis'],
    'lab': ['laboratory', 'test', 'blood work'],
    'diagnosis': ['disease', 'condition', 'disorder', 'illness'],
    'procedure': ['surgery', 'operation', 'intervention', 'treatment'],
    'vital': ['vitals', 'vital signs', 'measurements', 'monitoring'],
    'culture': ['microbiology', 'organism', 'infection', 'bacteria'],
    'time': ['date', 'when', 'period', 'duration'],
    'patient': ['subject', 'individual', 'case'],
    'admission': ['admit', 'hospitalization', 'hospital stay'],
    'discharge': ['release', 'hospital exit', 'leaving hospital'],
    'icu': ['intensive care', 'critical care', 'intensive care unit'],
    'antibiotic': ['antimicrobial', 'antibacterial', 'anti-infective']
}


def expand_query(query: str) -> List[str]:
    expanded = {query}
    q = query.lower()

    for k, variants in QUERY_EXPANSIONS.items():
        if k in q:
            for v in variants:
                expanded.add(q.replace(k, v))

    return list(expanded)


class MIMICColumnRetriever:
    def __init__(
        self,
        faiss_index_path: str = "graph/faiss_index.bin",
        meta_path: str = "graph/faiss_meta.json"
    ):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.column_names = meta["column_names"]
        self.column_metadata = meta["column_metadata"]

        hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if hf_token is None:
            raise RuntimeError(
                "HUGGINGFACE_HUB_TOKEN not found. "
                "Please export HUGGINGFACE_HUB_TOKEN=hf_xxx or run `hf auth login`"
            )

        print("Loading embedding model (bge-base-v1.5)...")
        self.model = SentenceTransformer(
            "BAAI/bge-base-en-v1.5",
            token=hf_token,
            device="cpu"
        )

        print("Loading FAISS index...")
        self.faiss_index = faiss.read_index(faiss_index_path)

        print("Building schema graph...")
        self.schema_graph = build_schema_graph()

    def retrieve_dense(self, query: str, top_k: int = 10) -> List[Dict]:
        q_emb = self.model.encode([query], convert_to_numpy=True)
        D, I = self.faiss_index.search(q_emb, top_k)

        # FAISS uses L2 distance → convert to similarity
        sims = -D[0]

        results = []
        for idx, col_idx in enumerate(I[0]):
            results.append({
                "column_name": self.column_names[col_idx],
                "similarity_score": float(sims[idx]),
                "tables": self.column_metadata[col_idx]["tables"],
                "description": self.column_metadata[col_idx]["description"],
            })

        return results

    def retrieve_with_expansion(self, query: str, top_k: int = 10) -> List[Dict]:
        merged = {}

        for q in expand_query(query):
            for r in self.retrieve_dense(q, top_k):
                name = r["column_name"]
                if (
                    name not in merged
                    or r["similarity_score"] > merged[name]["similarity_score"]
                ):
                    merged[name] = r

        return list(merged.values())

    def rerank(
        self,
        results: List[Dict],
        sim_weight: float = 0.7,
        coh_weight: float = 0.3,
    ) -> List[Dict]:

        table_freq = Counter(t for r in results for t in r["tables"])
        max_freq = max(table_freq.values(), default=1)

        for r in results:
            coherence = max(table_freq[t] / max_freq for t in r["tables"])
            r["final_score"] = (
                sim_weight * r["similarity_score"] + coh_weight * coherence
            )

        return sorted(results, key=lambda x: x["final_score"], reverse=True)

    def shortest_table_set(self, tables: List[str]) -> set:
        G = self.schema_graph
        keep_tables = set()

        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                try:
                    path = nx.shortest_path(G, tables[i], tables[j])
                    keep_tables.update(path)
                except nx.NetworkXNoPath:
                    pass

        return keep_tables

    def filter_by_dijkstra(self, results: List[Dict]) -> List[Dict]:
        candidate_tables = list(set(t for r in results for t in r["tables"]))
        keep_tables = self.shortest_table_set(candidate_tables)

        if not keep_tables:
            return results

        return [
            r for r in results
            if any(t in keep_tables for t in r["tables"])
        ]

    def organize_by_table(self, columns: List[Dict]) -> Dict[str, Dict]:
        table_data = defaultdict(lambda: {'columns': [], 'total_score': 0.0})

        for col in columns:
            primary_table = col['tables'][0] if col['tables'] else None
            if primary_table:
                score = col.get('final_score', col['similarity_score'])
                table_data[primary_table]['columns'].append({
                    'name': col['column_name'],
                    'description': col['description'],
                    'score': score
                })
                table_data[primary_table]['total_score'] += score

        # Sort tables and columns
        sorted_tables = dict(sorted(
            table_data.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        ))

        for t in sorted_tables:
            sorted_tables[t]['columns'].sort(
                key=lambda x: x['score'],
                reverse=True
            )

        return sorted_tables

    def log_columns(self, title: str, columns: List[Dict]):
        print(f"\n{'=' * 20} {title} {'=' * 20}")
        for c in columns:
            score = c.get("final_score", c["similarity_score"])
            print(
                f"- {c['column_name']} | "
                f"score={score:.3f} | "
                f"tables={c['tables']}"
            )

    def rag_retrieve(self, query: str, top_k: int = 15) -> Dict:
        # 1. Retrieve + expansion
        results = self.retrieve_with_expansion(query, top_k=top_k)

        # 2. Re-rank
        reranked = self.rerank(results)

        # 3. Global TOP-K
        reranked = reranked[:top_k]
        self.log_columns("Top-K Columns After Rerank", reranked)

        # 4. Dijkstra pruning
        filtered = self.filter_by_dijkstra(reranked)
        self.log_columns("Columns After Dijkstra", filtered)

        # 5. Table-centric format
        tables_info = self.organize_by_table(filtered)

        # 6. Backward-compatible lists
        all_columns = []
        all_tables = set()

        for table_name, table_data in tables_info.items():
            all_tables.add(table_name)
            for col in table_data['columns']:
                all_columns.append(col['name'])

        return {
            "tables_info": tables_info,
            "columns": all_columns,
            "tables": sorted(all_tables),
            "join_paths": describe_join_paths(all_tables),
            "raw": filtered
        }

    def format_for_llm_prompt(self, table_data: Dict[str, Dict]) -> str:
        lines = []
        lines.append("You are given the database schema below.")
        lines.append("Use ONLY the tables and columns listed.\n")

        for table, info in table_data.items():
            lines.append(f"TABLE {table}:")
            lines.append("-" * (7 + len(table)))
            for col in info["columns"]:
                desc = col["description"].replace("\n", " ")
                lines.append(f"- {col['name']}: {desc}")
            lines.append("")

        return "\n".join(lines)



if __name__ == "__main__":
    retriever = MIMICColumnRetriever(
        faiss_index_path="graph/faiss_index.bin",
        meta_path="graph/faiss_meta.json"
    )

    query = "What medicines did patient A use during 2014?"
    result = retriever.rag_retrieve(query)

    print("\n" + "=" * 80)
    print("RESULT STRUCTURE")
    print("=" * 80)
    print("Tables:", result["tables"])
    print("Columns:", result["columns"])
