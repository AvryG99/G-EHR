# Full evaluation after RAG/JOIN context updates

All 1287/1287 questions are present; no unscored comparisons remain.

- Correct arrays: 778/1287 (60.45%).
- Successful SQL executions: 1265/1287 (98.29%).
- Scan-budget failures: 0.
- Agent timeouts: 9, counted as incorrect.

The agent generated and executed SQL only. Grading compares raw arrays with annotated spans using gpt-4o-mini and rejects provably unscoped OR branches. Whole notes containing explicit requested evidence count as answer-bearing data. This measures evidence coverage, not human-verified extractive accuracy.

| Level | Tables | Questions | Correct | Accuracy |
|---|---|---:|---:|---:|
| 1 | 1 | 1073 | 661 | 61.60% |
| 2 | 2 | 194 | 115 | 59.28% |
| 3 | 3 | 8 | 2 | 25.00% |
| 4 | 4+ | 2 | 0 | 0.00% |

10 questions could not be assigned a level because SQL was missing or invalid. Levels count distinct tables in generated SQL, not minimum required tables.

Budget: 12 GB ordinary queries, 30 GB queries referencing noteevents/chartevents. Input and code hashes were verified unchanged during the run. CSV IDs and both JSON-array fields round-trip correctly.

Artifacts: `rag_v2_full_results.csv`, `rag_v2_full_summary.json`, `rag_v2_full_difficulty_summary.json`, `rag_v2_full_failure_analysis.json`, `rag_v2_full_manifest.json`, `rag_v2_full_verification.json`.
