# EHRSQL local mode

This mode targets the cleaned, shuffled MIMIC-III SQLite database bundled in
`ehrsql-ehragent/mimic_iii`. It is separate from the original MIMIC-III
BigQuery mode. Its schema is loaded from the official Spider-style
`ehrsql-ehragent/tables.json`; it intentionally includes `admissions.age`, a
`cost` table, and `charttime` in the ICD event tables.

Interactive local query:

```bash
python main.py -ehrsql
```

Evaluate all entries in `ehrsql-ehragent/mimic_iii/valid.json`:

```bash
python main.py -ehrsql --evaluate \
  --workers 16 \
  --output-prefix evaluation/ehrsql_valid
```

The evaluator checkpoints each prediction in JSONL and exports CSV plus a JSON
summary. Re-running the same command resumes missing IDs and re-exports sorted
results. It follows the official EHRSQL execution comparison: replace the fixed
`current_time` with `2105-12-31 23:59:00`, execute gold and predicted SQLite,
stringify and sort at most the first 100 tuples, then compare the results. It
reports answerability precision/recall/F1, execution precision/recall/F1,
overall success rate, and completion rate on answerable questions.

The model receives four lexical nearest examples from `train.json`. Validation
SQL and gold results are used only after prediction for evaluation. A prediction
of exactly `null` means the question is unanswerable from the cleaned schema.
