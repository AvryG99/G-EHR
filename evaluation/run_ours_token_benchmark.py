"""Run the proposed SQL pipeline with per-question OpenAI token telemetry."""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

from ehrsql.assistant import EHRSQLAssistant
from ehrsql.executor import execute, official_answer, post_process_sql
from llm.llm_client import LLMClient
from utils.config import load_project_env


FIELDS = [
    "id", "question", "template", "gold_answer", "predicted_answer",
    "predicted_sql", "correct", "completed", "difficulty", "prompt_tokens",
    "completion_tokens", "total_tokens", "llm_calls", "elapsed_seconds", "error",
]


def difficulty(query: str) -> int:
    count = len(set(re.findall(r"\bfrom\s+(\w+)\b", query, re.I)))
    return min(4, max(1, count))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--graph-rag", action="store_true")
    args = parser.parse_args()
    load_project_env()

    data = json.loads(Path(args.data).read_text())
    if args.limit is not None:
        data = data[:args.limit]
    output = Path(args.output)
    checkpoint = output.with_suffix(".jsonl")
    existing = [json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    completed_ids = {row["id"] for row in existing}

    llm = LLMClient(args.model, temperature=0)
    llm.client = llm.client.with_options(timeout=120, max_retries=1)
    retriever = None
    if args.graph_rag:
        from ehrsql.graph_retriever import EHRSQLGraphRetriever
        retriever = EHRSQLGraphRetriever()
    assistant = EHRSQLAssistant(llm=llm, max_retry=3, max_fewshot=4, retriever=retriever)
    records = list(existing)
    for item in data:
        if item["id"] in completed_ids:
            continue
        started = time.monotonic()
        llm.reset_usage()
        error = ""
        predicted_sql = ""
        predicted = "error_pred"
        try:
            predicted_sql, result = assistant.query(item["question"])
            if predicted_sql.strip().lower() == "null":
                predicted = "null"
            elif result["success"]:
                predicted = official_answer(result["rows"])
            else:
                error = str(result.get("error") or "execution error")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        gold = official_answer(execute(post_process_sql(item["query"])))
        record = {
            "id": item["id"], "question": item["question"], "template": item["template"],
            "gold_answer": gold, "predicted_answer": predicted, "predicted_sql": predicted_sql,
            "correct": gold == predicted, "completed": predicted != "error_pred",
            "difficulty": difficulty(item["query"]), **llm.usage,
            "elapsed_seconds": round(time.monotonic() - started, 3), "error": error,
        }
        records.append(record)
        with checkpoint.open("a") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"OURS_PROGRESS {len(records)}/{len(data)} correct={sum(r['correct'] for r in records)} "
              f"tokens={sum(r['total_tokens'] for r in records)}", flush=True)

    with output.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(records)
    summary = {
        "model": args.model, "total": len(records), "correct": sum(r["correct"] for r in records),
        "accuracy_percent": 100 * sum(r["correct"] for r in records) / max(1, len(records)),
        "completed": sum(r["completed"] for r in records),
        "prompt_tokens": sum(r["prompt_tokens"] for r in records),
        "completion_tokens": sum(r["completion_tokens"] for r in records),
        "total_tokens": sum(r["total_tokens"] for r in records),
        "llm_calls": sum(r["llm_calls"] for r in records),
    }
    output.with_name(output.stem + "_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
