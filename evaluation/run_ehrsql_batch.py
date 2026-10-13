"""Evaluate SQL generation on the local cleaned EHRSQL validation set."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
from pathlib import Path
import threading
import time

from ehrsql.executor import execute, official_answer, post_process_sql
from ehrsql.schema import VALID_PATH
from utils.config import load_project_env


FIELDS = ["id", "question", "is_impossible", "gold_sql", "predicted_sql",
          "gold_result", "predicted_result", "correct", "executable",
          "abstained", "error", "elapsed_seconds"]


def official_metrics(records: list[dict]) -> dict:
    predicted_answerable = [row for row in records if not row["abstained"]]
    gold_answerable = [row for row in records if not row["is_impossible"]]
    pa = sum(not row["is_impossible"] for row in predicted_answerable) / max(1, len(predicted_answerable))
    ra = sum(not row["abstained"] for row in gold_answerable) / max(1, len(gold_answerable))
    pe = sum(row["correct"] for row in predicted_answerable) / max(1, len(predicted_answerable))
    re = sum(row["correct"] for row in gold_answerable) / max(1, len(gold_answerable))
    f1 = lambda p, r: 2 * p * r / (p + r) if p + r else 0
    answerable_correct = sum(row["correct"] for row in gold_answerable)
    unanswerable = [row for row in records if row["is_impossible"]]
    unanswerable_correct = sum(row["correct"] for row in unanswerable)
    true_answerable = sum(not row["is_impossible"] and not row["abstained"] for row in records)
    true_unanswerable = sum(row["is_impossible"] and row["abstained"] for row in records)
    false_answerable = sum(row["is_impossible"] and not row["abstained"] for row in records)
    false_unanswerable = sum(not row["is_impossible"] and row["abstained"] for row in records)
    return {
        "total": len(records),
        "correct": sum(row["correct"] for row in records),
        "success_rate_percent": 100 * sum(row["correct"] for row in records) / max(1, len(records)),
        "completion_rate_percent": 100 * sum(row["executable"] for row in gold_answerable) / max(1, len(gold_answerable)),
        "answerable_gold": len(gold_answerable),
        "unanswerable_gold": len(records) - len(gold_answerable),
        "answerable_correct": answerable_correct,
        "answerable_execution_accuracy_percent": 100 * answerable_correct / max(1, len(gold_answerable)),
        "unanswerable_correct": unanswerable_correct,
        "unanswerable_abstention_accuracy_percent": 100 * unanswerable_correct / max(1, len(unanswerable)),
        "answerability_confusion": {
            "true_answerable": true_answerable, "true_unanswerable": true_unanswerable,
            "false_answerable": false_answerable, "false_unanswerable": false_unanswerable,
        },
        "execution_errors": sum(not row["executable"] and not row["abstained"] for row in records),
        "precision_ans": round(100 * pa, 2), "recall_ans": round(100 * ra, 2),
        "f1_ans": round(100 * f1(pa, ra), 2),
        "precision_exec": round(100 * pe, 2), "recall_exec": round(100 * re, 2),
        "f1_exec": round(100 * f1(pe, re), 2),
        "comparison": "Official EHRSQL execution-result normalization: sorted stringified tuples, first 100 rows; current_time fixed to 2105-12-31 23:59:00.",
    }


def run_batch(output_prefix="evaluation/ehrsql_valid", workers=16, limit=None):
    load_project_env()
    from main import create_ehrsql_assistant
    assistant = create_ehrsql_assistant()
    assistant.llm.client = assistant.llm.client.with_options(timeout=120, max_retries=1)
    data = json.loads(VALID_PATH.read_text())
    if limit is not None:
        data = data[:limit]
    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = Path(str(prefix) + "_results.jsonl")
    existing = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    completed = {row["id"] for row in existing}
    lock = threading.Lock()

    def evaluate(item):
        started = time.monotonic()
        impossible = bool(item.get("is_impossible"))
        gold_sql = str(item["query"])
        gold = "null" if impossible else official_answer(execute(post_process_sql(gold_sql)))
        predicted_sql, result = assistant.query(item["question"])
        abstained = predicted_sql.strip().lower() == "null"
        if abstained:
            predicted = "null"
        elif result["success"]:
            predicted = official_answer(result["rows"])
        else:
            predicted = "error_pred"
        return {
            "id": item["id"], "question": item["question"],
            "is_impossible": impossible, "gold_sql": gold_sql,
            "predicted_sql": predicted_sql, "gold_result": gold,
            "predicted_result": predicted, "correct": gold == predicted,
            "executable": bool(result["success"] and not abstained),
            "abstained": abstained, "error": result.get("error"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }

    records = list(existing)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate, item): item for item in data if item["id"] not in completed}
        for future in as_completed(futures):
            try:
                record = future.result()
            except Exception as error:
                item = futures[future]
                record = {"id": item["id"], "question": item["question"],
                          "is_impossible": bool(item.get("is_impossible")),
                          "gold_sql": str(item["query"]), "predicted_sql": "",
                          "gold_result": "", "predicted_result": "error_pred",
                          "correct": False, "executable": False, "abstained": False,
                          "error": str(error), "elapsed_seconds": None}
            with lock:
                with checkpoint.open("a") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                records.append(record)
                Path(str(prefix) + "_summary.json").write_text(
                    json.dumps(official_metrics(records), indent=2)
                )
                print(f"EHRSQL_PROGRESS {len(records)}/{len(data)}", flush=True)

    order = {item["id"]: index for index, item in enumerate(data)}
    records.sort(key=lambda row: order[row["id"]])
    with Path(str(prefix) + "_results.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(records)
    summary = official_metrics(records)
    Path(str(prefix) + "_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-prefix", default="evaluation/ehrsql_valid")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    run_batch(args.output_prefix, args.workers, args.limit)
