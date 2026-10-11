import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict


class FewshotRetriever:
    def __init__(
        self,
        memory_path: str,
        model_name: str = "BAAI/bge-base-en-v1.5"
    ):
        self.model = SentenceTransformer(model_name)

        with open(memory_path, "r", encoding="utf-8") as f:
            self.memory: List[Dict] = json.load(f)

        self.questions = [item["question"] for item in self.memory]

        self.embeddings = self.model.encode(
            self.questions,
            normalize_embeddings=True,
            show_progress_bar=False
        )

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        query = query.strip()

        query_emb = self.model.encode(
            query,
            normalize_embeddings=True
        )

        scores = np.dot(self.embeddings, query_emb)
        top_idx = np.argsort(scores)[::-1][:top_k]

        return [self.memory[i] for i in top_idx]
