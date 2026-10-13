"""Build a self-contained HTML dashboard comparing EHRAgent and our pipeline."""
from __future__ import annotations

import argparse
import csv
import html
import json
import statistics
from pathlib import Path


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key in ("difficulty", "prompt_tokens", "completion_tokens", "total_tokens", "llm_calls"):
            row[key] = int(float(row.get(key) or 0))
        for key in ("correct", "completed"):
            row[key] = str(row.get(key, "")).lower() == "true"
    return rows


def stats(rows):
    tokens = [r["total_tokens"] for r in rows]
    calls = [r["llm_calls"] for r in rows]
    correct = sum(r["correct"] for r in rows)
    return {
        "n": len(rows), "correct": correct,
        "accuracy": 100 * correct / max(1, len(rows)),
        "tokens": sum(tokens), "avg_tokens": sum(tokens) / max(1, len(rows)),
        "median_tokens": statistics.median(tokens) if tokens else 0,
        "calls": sum(calls), "avg_calls": sum(calls) / max(1, len(rows)),
        "tokens_per_correct": sum(tokens) / max(1, correct),
    }


def by_level(rows):
    return {str(level): stats([r for r in rows if r["difficulty"] == level]) for level in range(1, 5)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ehragent", default="evaluation/ehragent_gpt4o_mini.csv")
    parser.add_argument("--ours", default="evaluation/ours_graph_gpt4o_mini.csv")
    parser.add_argument("--direct", default="evaluation/ours_gpt4o_mini.csv")
    parser.add_argument("--output", default="evaluation/ehragent_token_dashboard.html")
    args = parser.parse_args()
    ehr = read_csv(args.ehragent)
    ours = read_csv(args.ours)
    direct = read_csv(args.direct) if Path(args.direct).exists() else []
    emap, omap = ({r["id"]: r for r in rows} for rows in (ehr, ours))
    ids = sorted(set(emap) & set(omap))
    combined = []
    for qid in ids:
        e, o = emap[qid], omap[qid]
        combined.append({
            "id": qid, "question": o.get("question") or e.get("question"),
            "level": o["difficulty"],
            "ours_correct": o["correct"], "ours_tokens": o["total_tokens"], "ours_calls": o["llm_calls"],
            "ehr_correct": e["correct"], "ehr_tokens": e["total_tokens"], "ehr_calls": e["llm_calls"],
            "token_delta": e["total_tokens"] - o["total_tokens"],
        })
    payload = {
        "model": "gpt-4o-mini", "ours": stats(ours), "direct": stats(direct),
        "ehragent": stats(ehr),
        "ours_levels": by_level(ours), "ehragent_levels": by_level(ehr), "rows": combined,
        "coverage": {"paired": len(ids), "ours": len(ours), "ehragent": len(ehr)},
    }
    safe = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Token Efficiency Benchmark</title>
<style>
:root{--bg:#07111f;--card:#101e31;--line:#263750;--text:#e8f0fa;--muted:#92a5bd;--ours:#40d9a3;--ehr:#ffad66}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(145deg,#07111f,#0c1829);color:var(--text);font:14px Inter,system-ui,sans-serif}.wrap{max-width:1400px;margin:auto;padding:30px}.eyebrow{color:var(--ours);font-weight:700;letter-spacing:.12em;text-transform:uppercase}h1{font-size:34px;margin:8px 0}.sub{color:var(--muted);max-width:900px;line-height:1.6}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:25px 0}.card,.panel{background:rgba(16,30,49,.92);border:1px solid var(--line);border-radius:14px;padding:18px}.label{color:var(--muted);font-size:12px;text-transform:uppercase}.value{font-size:28px;font-weight:750;margin-top:5px}.good{color:var(--ours)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.panel h2{margin:0 0 16px}.barrow{display:grid;grid-template-columns:90px 1fr 82px;gap:10px;align-items:center;margin:11px 0}.track{height:11px;background:#07111f;border-radius:10px;overflow:hidden}.bar{height:100%;border-radius:10px}.ours{background:var(--ours)}.ehr{background:var(--ehr)}.legend span{display:inline-block;margin-right:20px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}input,select{background:#07111f;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:9px;margin:0 8px 12px 0}table{width:100%;border-collapse:collapse;font-size:12px}th{position:sticky;top:0;background:#15253a;text-align:left}th,td{padding:9px;border-bottom:1px solid var(--line)}tr:hover{background:#14243a}.yes{color:var(--ours)}.no{color:#ff7285}.tablewrap{max-height:650px;overflow:auto}.note{color:var(--muted);font-size:12px;line-height:1.5;margin-top:18px}@media(max-width:900px){.cards,.grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){.cards,.grid{grid-template-columns:1fr}.wrap{padding:16px}}
</style></head><body><main class="wrap"><div class="eyebrow">Controlled model comparison</div><h1>EHRAgent vs Proposed Method</h1><p class="sub">Both systems use <b>gpt-4o-mini</b>. Token totals include every measured LLM stage. EHRAgent includes knowledge retrieval, iterative agent calls and error debugging; the proposed pipeline includes SQL generation and failure-triggered repair.</p>
<section class="cards" id="cards"></section><section class="grid"><div class="panel"><h2>Accuracy by difficulty</h2><div class="legend"><span><i class="dot ours"></i>Proposed (direct SQL)</span><span><i class="dot ehr"></i>EHRAgent</span></div><div id="accuracy"></div></div><div class="panel"><h2>Average tokens by difficulty</h2><div id="tokens"></div></div></section>
<section class="panel" style="margin-top:16px"><h2>Per-question comparison</h2><input id="search" placeholder="Search question or ID"><select id="level"><option value="">All levels</option><option>1</option><option>2</option><option>3</option><option>4</option></select><select id="outcome"><option value="">All outcomes</option><option value="ours_only">Only ours correct</option><option value="ehr_only">Only EHRAgent correct</option><option value="both">Both correct</option><option value="neither">Neither correct</option></select><div class="tablewrap"><table><thead><tr><th>Level</th><th>Question</th><th>Ours ✓</th><th>Ours tokens</th><th>Ours calls</th><th>EHRAgent ✓</th><th>EHRAgent tokens</th><th>EHRAgent calls</th><th>Tokens saved</th></tr></thead><tbody id="rows"></tbody></table></div></section>
<p class="note">Accuracy follows each implementation's released evaluator: EHRAgent uses its answer-containment judge, while the proposed SQL pipeline uses exact normalized execution results. This dashboard establishes model parity and resource usage; a strict evaluator-parity table should be reported separately for a fully controlled accuracy claim. Difficulty is the number of distinct physical tables in the gold query, capped at Level 4.</p></main>
<script id="data" type="application/json">""" + safe + """</script><script>
const D=JSON.parse(document.getElementById('data').textContent),fmt=n=>new Intl.NumberFormat().format(Math.round(n)),pct=n=>n.toFixed(2)+'%';
const O=D.ours,E=D.ehragent,B=D.direct,saved=E.tokens?100*(E.tokens-O.tokens)/E.tokens:0;
document.getElementById('cards').innerHTML=`<div class=card><div class=label>Proposed accuracy</div><div class="value good">${pct(O.accuracy)}</div><small>${O.correct}/${O.n}</small></div><div class=card><div class=label>EHRAgent accuracy</div><div class=value>${pct(E.accuracy)}</div><small>${E.correct}/${E.n}</small></div><div class=card><div class=label>Token reduction</div><div class="value good">${pct(saved)}</div><small>${fmt(O.tokens)} vs ${fmt(E.tokens)}</small></div><div class=card><div class=label>Average LLM calls</div><div class=value>${O.avg_calls.toFixed(2)} / ${E.avg_calls.toFixed(2)}</div><small>Proposed / EHRAgent</small></div>`;
function bars(target,key,maxFn,labelFn){const el=document.getElementById(target);for(let l=1;l<=4;l++){const a=D.ours_levels[l][key],b=D.ehragent_levels[l][key],m=maxFn(a,b);el.innerHTML+=`<div class=barrow><b>Level ${l}</b><div><div class=track><div class="bar ours" style="width:${m(a)}%"></div></div><div class=track style="margin-top:4px"><div class="bar ehr" style="width:${m(b)}%"></div></div></div><span>${labelFn(a)}<br>${labelFn(b)}</span></div>`}}
bars('accuracy','accuracy',()=>x=>x,pct);let mt=1;for(let l=1;l<=4;l++)mt=Math.max(mt,D.ours_levels[l].avg_tokens,D.ehragent_levels[l].avg_tokens);bars('tokens','avg_tokens',()=>x=>100*x/mt,x=>fmt(x));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function render(){const q=search.value.toLowerCase(),lv=level.value,out=outcome.value;rows.innerHTML=D.rows.filter(r=>(!q||(r.question+' '+r.id).toLowerCase().includes(q))&&(!lv||r.level==lv)&&(!out||(out==='ours_only'&&r.ours_correct&&!r.ehr_correct)||(out==='ehr_only'&&!r.ours_correct&&r.ehr_correct)||(out==='both'&&r.ours_correct&&r.ehr_correct)||(out==='neither'&&!r.ours_correct&&!r.ehr_correct))).map(r=>`<tr><td>L${r.level}</td><td title="${esc(r.id)}">${esc(r.question)}</td><td class=${r.ours_correct?'yes':'no'}>${r.ours_correct?'✓':'×'}</td><td>${fmt(r.ours_tokens)}</td><td>${r.ours_calls}</td><td class=${r.ehr_correct?'yes':'no'}>${r.ehr_correct?'✓':'×'}</td><td>${fmt(r.ehr_tokens)}</td><td>${r.ehr_calls}</td><td class=${r.token_delta>0?'yes':'no'}>${fmt(r.token_delta)}</td></tr>`).join('')}search.oninput=level.onchange=outcome.onchange=render;render();
</script></body></html>"""
    Path(args.output).write_text(page, encoding="utf-8")
    Path(args.output).with_suffix(".json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(json.dumps({k: payload[k] for k in ("coverage", "ours", "direct", "ehragent")}, indent=2))


if __name__ == "__main__":
    main()
