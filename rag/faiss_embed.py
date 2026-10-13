from graph.tables import unique_columns
import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def main(
    json_file_path="graph/unique_columns.json",
    faiss_index_path="graph/faiss_index.bin",
    meta_path="graph/faiss_meta.json"
):
    columns_data = unique_columns()
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(columns_data, f, ensure_ascii=False, indent=2)

    hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    if hf_token is None:
        raise RuntimeError(
            "HUGGINGFACE_HUB_TOKEN not found. "
            "Please export HUGGINGFACE_HUB_TOKEN=hf_xxx or run `hf auth login`"
        )

    print("Loading embedding model (bge-base-v1.5)...")
    model = SentenceTransformer(
        "BAAI/bge-base-en-v1.5",
        token=hf_token,
        device="cpu"
    )

    column_names = []
    column_texts = []
    column_metadata = []

    for col_name, info in columns_data.items():
        column_names.append(col_name)
        column_metadata.append(info)
        text = (
            f"{col_name}. "
            f"{info['description']}. "
            f"Found in tables: {', '.join(info['tables'])}"
        )
        column_texts.append(text)

    print("Encoding column embeddings...")
    embeddings = model.encode(
        column_texts,
        convert_to_numpy=True,
        show_progress_bar=True,
    )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, faiss_index_path)
    print(f"FAISS index saved to {faiss_index_path}")

    meta = {
        "column_names": column_names,
        "column_metadata": column_metadata
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Metadata saved to {meta_path}")
    
if __name__ == "__main__":
    main()