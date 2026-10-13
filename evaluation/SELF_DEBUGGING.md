# Result review and semantic SQL repair

`MedicalDatabaseAssistant.query()` executes SQL, reviews the returned evidence,
and performs up to two semantic revisions when the review identifies concrete
defects. It still returns `(sql, result)` without a clinical prose answer.

The reviewer receives the question, allowed RAG schema, SQL and returned array.
It receives no benchmark reference answer or original source passage. Large
arrays have a 60,000-character evidence preview with an explicit truncation
flag. The original returned array is kept intact. A reviewer verdict is a model
assessment, not proof of clinical correctness or evidence completeness.

Set `MIMIC_SEMANTIC_RETRIES=0` to disable result review for a baseline. Values
`1` and `2` enable review with that maximum number of semantic revisions;
the default is `2`. Each revision also uses the existing SQL error repair
budget. Billing limits apply separately to each executed query.

Results contain `review_status` and `review_history`. Possible final statuses:
`accepted`, `insufficient_evidence`, `revision_limit`, `review_unavailable`,
and `revision_failed`. Initial execution failures skip review. A failed revision
keeps the most recent successful SQL and array, with the failure recorded.
Scoped semantic revisions require explicit ID predicates at physical sources,
including CTE/UNION branches; this conservative guard may reject queries that
apply otherwise valid scoping only in an outer SELECT.

Exact review and repair prompts and decisions are recorded in the configured
SQL prompt log under `result_review`, `result_review_decision`, and
`semantic_revision`. Batch JSONL/CSV also persist the status and history.
Evaluation comparison remains a separate operation with reference answers;
its verdict is never fed back into this repair loop.

For a controlled comparison, use the same question IDs and separate output
prefixes with `MIMIC_SEMANTIC_RETRIES=0` versus `2`. Accuracy has not yet been
measured for this feature; passing workflow tests does not demonstrate an
accuracy improvement.
