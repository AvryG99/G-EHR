# BigQuery agent evaluation

Input: `test.final.json` (1,287 questions, 36 note passages).

The numeric document titles were verified against
`physionet-data.mimiciii_notes.noteevents.row_id`. All 36 supplied contexts
match the retrieved note when case, whitespace and punctuation are removed.
This establishes subject/admission IDs; the annotated passages and answers
are never included in the evaluated agent's input.

Each question runs independently with the verified patient/admission scope,
through the existing RAG, SQL generation/retry, BigQuery execution and answer
workflow. The agent's 1 GB query limit remains unchanged. It uses the clinical
dataset, which does not include the separate notes table. No agent fixes are
made during this baseline evaluation.

Scoring:

- Normalized exact match and token F1 against the best annotated answer span.
- Semantic correctness judged by `gpt-4o-mini` with the original question,
  source note, reference spans and candidate answer. This is automated grading,
  not human-verified accuracy.
- SQL failures count as incorrect. Judge errors are explicitly recorded.

Both the agent and judge use `gpt-4o-mini`; this limits independence of grading.
The source benchmark is extractive note QA rather than a SQL execution
benchmark, so exact match naturally penalizes paraphrases and affirmative
answers. Semantic accuracy should be interpreted with those limitations.

Run or resume:

```sh
python -m evaluation.run_bigquery_batch --workers 16
```

The script uses `.env`, local FAISS artifacts, and existing ADC credentials.
Use `--limit 4` for a pilot. Completed IDs are skipped when resuming.

Outputs:

- `note_mapping.json`: verified patient/admission scope per note.
- `bigquery_results.jsonl`: answer, SQL, execution status, limited returned rows,
  reference answers, scoring and grading rationale for every question.
- `bigquery_summary.json`: live checkpoint and aggregate metrics.
- `batch_runtime.log`: redirected runtime output.

Fetched notes, mappings and raw evaluation results are local ignored artifacts.
The notes mapping query was separately authorized to scan up to 5 GB; its dry
run estimated 3,856,218,765 bytes. The batch never raises the agent's per-query
limit.

## SQL-only result-array evaluation

`python -m evaluation.run_array_batch --workers 16` runs the agent's `query()`
method; it never calls `generate_natural_response`. Output artifacts are
`array_results.csv`, `array_results.jsonl`, and `array_summary.json`.
The CSV stores full returned arrays, SQL, reference spans, correctness verdict
and rationale, failures, scanned bytes and selected billing limit.
The separately authorized comparator is `gpt-4o-mini`, grading raw arrays rather
than agent prose. Whole notes containing explicit requested evidence count as
answer-bearing data, so this measures result evidence coverage rather than
concise extractive answer accuracy. Semantic grading is model-based.
The agent uses the updated 1 GB ordinary / 10 GB notes-or-chart scan budgets.

Completed SQL-only run: 1,287 records, 579 semantically correct (44.99%),
1,227 successful executions (95.34%). Two tasks returned no array after
repeated stalls and a fresh retry exceeding five minutes; they are retained
as execution timeouts. One array exceeded comparator context length and was
reviewed in six intact-row chunks. `comparison_method` and `outcome` in the
final CSV distinguish these cases. The CSV has been validated for unique IDs
and JSON round trips of full result and reference arrays.

Full rerun after notes-context fixes uses prefix `evaluation/notes_full`:

```sh
python -m evaluation.run_array_batch --workers 16 --output-prefix evaluation/notes_full --task-timeout 300
```

Every active task has a 300-second deadline, excluding time queued for a worker.
Agent execution timeouts count as failed queries. Comparator timeouts remain
explicitly unscored until regraded. Completed records survive restarts.
Use `--ids-file` with a JSON list of question IDs for a targeted pilot.
Full result-array and reference data are stored in the prefix's CSV and JSONL.
The earlier `evaluation/array_*` baseline files are preserved.
