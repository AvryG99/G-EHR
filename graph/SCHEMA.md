# Original MIMIC-III schema

Source: https://lcp.mit.edu/mimic-schema-spy/mimic.mimiciii.xml

`mimiciii_schema.json` contains the 26 logical tables (324 columns), PostgreSQL
source types, nullable flags, row primary keys and explicit foreign keys.
Query `chartevents`; its 14 physical partitions are excluded.
`tables.py`, the graph, schema inspection and retrieval metadata share this source.
The runtime still generates BigQuery SQL and transpiles for local execution.

After installing requirements and setting HUGGINGFACE_HUB_TOKEN, rebuild the
retrieval embeddings from the repository root:

```sh
python -m rag.faiss_embed
```

The retriever rejects old cleaned-schema metadata until this rebuild succeeds.
Existing cleaned databases must separately be replaced with original MIMIC-III
data; these changes do not migrate database contents.
