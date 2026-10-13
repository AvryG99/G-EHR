"""Build a self-contained HTML report for the EHRSQL validation batch."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from ehrsql.schema import DATA_ROOT


def physical_tables(sql: str) -> list[str]:
    tree = sqlglot.parse_one(sql, read="sqlite")
    return sorted({source.name.lower() for scope in traverse_scope(tree)
                   for source in scope.sources.values() if isinstance(source, exp.Table)})


def bucket(record: dict) -> tuple[str, str]:
    if record["is_impossible"]:
        return "unanswerable", "Unanswerable"
    count = len(physical_tables(record["gold_sql"]))
    if count == 0:
        return "no_table", "No-table SQL"
    level = min(count, 4)
    return f"level_{level}", f"Level {level}"


def breakdown(records: list[dict]) -> dict:
    labels = {
        "level_1": "Level 1", "level_2": "Level 2", "level_3": "Level 3",
        "level_4": "Level 4", "no_table": "No-table SQL",
        "unanswerable": "Unanswerable",
    }
    groups = {key: [] for key in labels}
    for record in records:
        key, _ = bucket(record)
        groups[key].append(record)
    result = []
    for key in ("level_1", "level_2", "level_3", "level_4", "no_table", "unanswerable"):
        rows = groups[key]
        if key == "no_table" and not rows:
            continue
        correct = sum(row["correct"] for row in rows)
        result.append({
            "key": key, "label": labels[key], "table_rule": {
                "level_1": "1 table", "level_2": "2 tables", "level_3": "3 tables",
                "level_4": "4+ tables", "no_table": "0 tables",
                "unanswerable": "gold SQL = null",
            }[key],
            "questions": len(rows), "correct": correct,
            "incorrect": len(rows) - correct,
            "accuracy_percent": 100 * correct / len(rows) if rows else None,
            "executable": sum(row["executable"] for row in rows),
            "abstained": sum(row["abstained"] for row in rows),
        })
    return {"groups": result}


def pct(value):
    return "—" if value is None else f"{value:.2f}%"


def build_report(prefix: str) -> tuple[Path, Path]:
    path = Path(prefix + "_results.jsonl")
    records = [json.loads(line) for line in path.read_text().splitlines()]
    summary = json.loads(Path(prefix + "_summary.json").read_text())
    detail = breakdown(records)
    by_id = {record["id"]: record for record in records}
    ehragent_data = json.loads((DATA_ROOT / "mimic_iii" / "valid_preprocessed.json").read_text())
    ehragent_groups = {level: [] for level in range(1, 5)}
    for item in ehragent_data:
        # This is the exact regex used by EHRAgent's question_difficulty.py.
        count = len(set(re.findall(r'\bfrom\s+(\w+)\b', item["query"])))
        ehragent_groups[min(count, 4)].append(by_id[item["id"]])
    published = {1: 71.58, 2: 66.34, 3: 49.70, 4: 49.14}
    paper_rows = []
    for level in range(1, 5):
        group = ehragent_groups[level]
        ours = 100 * sum(row["correct"] for row in group) / len(group)
        paper_rows.append({"level": level, "questions": len(group), "correct": sum(row["correct"] for row in group),
                           "ours": ours, "paper": published[level], "delta": ours - published[level]})
    subset_correct = sum(row["correct"] for group in ehragent_groups.values() for row in group)
    subset_total = sum(map(len, ehragent_groups.values()))
    subset_completion = 100 * sum(row["executable"] for group in ehragent_groups.values() for row in group) / subset_total
    detail["ehragent_paper_comparison"] = {
        "current_subset_questions": subset_total, "current_subset_correct": subset_correct,
        "current_subset_success_rate": 100 * subset_correct / subset_total,
        "current_subset_completion_rate": subset_completion,
        "paper_questions": 580, "paper_success_rate": 58.97, "paper_completion_rate": 85.86,
        "levels": paper_rows,
        "warning": "Near-matched data, not yet a controlled head-to-head: current released subset has 581 rather than 580 questions, and model, input text, retrieval, interaction, and grading protocols differ.",
    }
    detail.update({
        "total": len(records), "correct": sum(row["correct"] for row in records),
        "overall_accuracy_percent": 100 * sum(row["correct"] for row in records) / len(records),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "difficulty_basis": "Distinct physical tables in gold SQL; CTE aliases and repeated references count once. Unanswerable questions have no SQL and are shown separately.",
    })
    json_path = Path(prefix + "_report.json")
    json_path.write_text(json.dumps(detail, indent=2))

    rows_html = "".join(
        f"<tr><td><span class='dot {g['key']}'></span>{escape(g['label'])}</td>"
        f"<td>{escape(g['table_rule'])}</td><td>{g['questions']:,}</td>"
        f"<td>{g['correct']:,}</td><td>{g['incorrect']:,}</td>"
        f"<td><div class='bar'><i style='width:{g['accuracy_percent'] or 0:.2f}%'></i></div>"
        f"<strong>{pct(g['accuracy_percent'])}</strong></td>"
        f"<td>{g['executable']:,}</td><td>{g['abstained']:,}</td></tr>"
        for g in detail["groups"]
    )
    confusion = summary["answerability_confusion"]
    errors = [row for row in records if row.get("error")]
    errors_html = "".join(
        f"<tr><td>{escape(row['id'])}</td><td>{escape(row['question'])}</td>"
        f"<td><code>{escape(row['error'])}</code></td></tr>" for row in errors
    ) or "<tr><td colspan='3'>No execution errors</td></tr>"
    paper_rows_html = "".join(
        f"<tr><td>Level {row['level']}</td><td>{row['questions']}</td>"
        f"<td>{row['ours']:.2f}%</td><td>{row['paper']:.2f}%</td>"
        f"<td class='positive'>+{row['delta']:.2f} pp</td></tr>" for row in paper_rows
    ) + (f"<tr class='total'><td>All</td><td>{subset_total}</td>"
         f"<td>{100 * subset_correct / subset_total:.2f}%</td><td>58.97%</td>"
         f"<td class='positive'>+{100 * subset_correct / subset_total - 58.97:.2f} pp</td></tr>")
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EHRSQL Validation Report</title><style>
:root{{--bg:#f4f7fb;--card:#fff;--ink:#172033;--muted:#697386;--line:#e5e9f0;--blue:#2f6fed;--green:#159570;--amber:#d98b18;--red:#d34c5c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:36px 24px 60px}}h1{{font-size:30px;margin:0 0 6px}}h2{{font-size:18px;margin:0 0 18px}}p{{color:var(--muted);margin:4px 0}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:26px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 3px 14px #18233a0a}}.metric b{{display:block;font-size:27px;margin-top:5px}}.metric span{{color:var(--muted)}}
.section{{margin-top:18px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px 10px;text-align:right;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){{text-align:left}}
.bar{{display:inline-block;width:90px;height:7px;background:#e7edf8;border-radius:8px;overflow:hidden;margin-right:9px;vertical-align:middle}}.bar i{{display:block;height:100%;background:linear-gradient(90deg,var(--blue),#6f9cff)}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--blue);margin-right:8px}}.unanswerable{{background:var(--amber)}}.no_table{{background:#8c6ad8}}code{{white-space:pre-wrap;word-break:break-word;font-size:12px}}.note{{padding:12px 14px;background:#eef4ff;border-left:3px solid var(--blue);border-radius:6px;margin-top:16px}}.warn{{background:#fff7e8;border-left-color:var(--amber)}}.small{{font-size:12px}}.positive{{color:var(--green);font-weight:700}}tr.total td{{font-weight:700;border-top:2px solid var(--line)}}a{{color:var(--blue)}}@media(max-width:800px){{.grid{{grid-template-columns:repeat(2,1fr)}}.scroll{{overflow:auto}}}}@media(max-width:480px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main class="wrap">
<h1>EHRSQL cleaned MIMIC-III</h1><p>Validation report · {len(records):,} questions · SQL-only local execution</p>
<div class="grid">
 <div class="card metric"><span>Overall accuracy</span><b>{summary['success_rate_percent']:.2f}%</b><small>{summary['correct']:,} / {summary['total']:,}</small></div>
 <div class="card metric"><span>Answerable accuracy</span><b>{summary['answerable_execution_accuracy_percent']:.2f}%</b><small>{summary['answerable_correct']:,} / {summary['answerable_gold']:,}</small></div>
 <div class="card metric"><span>Unanswerable accuracy</span><b>{summary['unanswerable_abstention_accuracy_percent']:.2f}%</b><small>{summary['unanswerable_correct']:,} / {summary['unanswerable_gold']:,}</small></div>
 <div class="card metric"><span>Execution F1</span><b>{summary['f1_exec']:.2f}%</b><small>Official EHRSQL-style comparison</small></div>
</div>
<section class="card section"><h2>Accuracy by difficulty</h2><div class="scroll"><table><thead><tr><th>Group</th><th>Gold requirement</th><th>Questions</th><th>Correct</th><th>Incorrect</th><th>Accuracy</th><th>Executable</th><th>Abstained</th></tr></thead><tbody>{rows_html}</tbody></table></div>
<p class="note small">Level is based on distinct physical tables required by the <b>gold SQL</b>. Level 4 means four or more tables. No-table SQL and unanswerable questions are displayed separately and are included in overall accuracy.</p></section>
<section class="grid section">
 <div class="card metric"><span>Completion rate</span><b>{summary['completion_rate_percent']:.2f}%</b><small>Executable plans / answerable questions</small></div>
 <div class="card metric"><span>Answerability F1</span><b>{summary['f1_ans']:.2f}%</b><small>P {summary['precision_ans']:.2f}% · R {summary['recall_ans']:.2f}%</small></div>
 <div class="card metric"><span>True answerable</span><b>{confusion['true_answerable']:,}</b><small>False unanswerable: {confusion['false_unanswerable']:,}</small></div>
 <div class="card metric"><span>True unanswerable</span><b>{confusion['true_unanswerable']:,}</b><small>False answerable: {confusion['false_answerable']:,}</small></div>
</section>
<section class="card section"><h2>Comparison with published EHRAgent (MIMIC-III)</h2>
<div class="scroll"><table><thead><tr><th>Difficulty</th><th>Current questions</th><th>Proposed method (Ours) SR</th><th>EHRAgent SR</th><th>Difference</th></tr></thead><tbody>{paper_rows_html}</tbody></table></div>
<p class="note warn small"><b>Use this as a preliminary cross-paper comparison, not yet a controlled leaderboard result.</b> The current official release has 581 answerable questions while EHRAgent reports 580. Our method uses GPT-4o-mini, paraphrased questions, four nearest training examples, direct SQLite generation and exact execution-result comparison. EHRAgent used GPT-4-0613, template questions, four initial demonstrations plus accumulated long-term memory, Python tool plans with up to 10 interactions, and substring-based answer judging. Published EHRAgent completion rate: 85.86%; our method on the current 581-question subset: {subset_completion:.2f}%.</p>
<p class="small">Sources: <a href="https://aclanthology.org/2024.emnlp-main.1245/">EHRAgent paper</a> · <a href="https://github.com/wshi83/EhrAgent">official code</a> · <a href="https://huggingface.co/datasets/wshi83/EHRAgent-mimic_iii">released data</a></p></section>
<section class="card section"><h2>Execution errors ({len(errors)})</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Question</th><th>Error</th></tr></thead><tbody>{errors_html}</tbody></table></div></section>
<section class="card section"><h2>Evaluation method</h2><p>Gold and predicted SQLite are executed against the same cleaned local database. Results are stringified and sorted for at most the first 100 rows. <code>current_time</code> is fixed at <code>2105-12-31 23:59:00</code>. A gold <code>null</code> is correct only when the model also abstains with <code>null</code>.</p><p class="small">Generated {escape(detail['generated_at'])}</p></section>
</main></body></html>"""
    html_path = Path(prefix + "_report.html")
    html_path.write_text(html)
    return html_path, json_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-prefix", default="evaluation/ehrsql_valid")
    args = parser.parse_args()
    html_path, json_path = build_report(args.output_prefix)
    print(html_path); print(json_path)
