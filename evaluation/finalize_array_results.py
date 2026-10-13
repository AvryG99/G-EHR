"""Validate and export batch records, including observed task timeouts."""
import csv
import json
from pathlib import Path
from evaluation.run_array_batch import FIELDS, summary

source=json.loads(Path('test.final.json').read_text())
expected={q['id']:q for d in source['data'] for p in d['paragraphs'] for q in p['qas']}
path=Path('evaluation/array_results.jsonl')
rows=[json.loads(line) for line in path.read_text().splitlines()]
assert len({r['id'] for r in rows})==len(rows)
missing=set(expected)-{r['id'] for r in rows}
# These tasks were observed stuck across both the full run and a fresh retry
# exceeding five minutes. Never synthesize a query result or generated SQL.
assert missing <= {'447','769'}, missing
mappings={m['title']:m for m in json.loads(Path('evaluation/note_mapping.json').read_text())}
for doc in source['data']:
 m=mappings[doc['title']]
 for paragraph in doc['paragraphs']:
  for q in paragraph['qas']:
   if q['id'] not in missing:continue
   rows.append({'id':q['id'],'note_row_id':m['row_id'],'subject_id':m['subject_id'],
                'hadm_id':m['hadm_id'],'question':q['question'],'sql':None,'executed_sql':None,
                'result_array':[],'reference_answers':[a['text'] for a in q['answers']],
                'execution_success':False,'row_count':0,'correct':False,
                'error':'Task timed out: no result array returned after more than 300 seconds on fresh retry; worker terminated.',
                'comparison_reason':'No array returned; execution timeout counts as incorrect.',
                'comparison_method':'execution_timeout','outcome':'timeout',
                'elapsed_seconds':None})
order={key:i for i,key in enumerate(expected)}
rows.sort(key=lambda r:order[r['id']])
fields=FIELDS+['comparison_method','outcome']
for r in rows:
 r.setdefault('comparison_method','model_semantic' if r['execution_success'] else 'execution_failure')
 r.setdefault('outcome','correct' if r['correct'] else 'incorrect' if r['execution_success'] else 'execution_error')
path.write_text(''.join(json.dumps(r,ensure_ascii=False,default=str)+'\n' for r in rows))
with Path('evaluation/array_results.csv').open('w',newline='',encoding='utf-8-sig') as stream:
 writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
 for r in rows:
  writer.writerow({key:json.dumps(r.get(key),ensure_ascii=False,default=str)
                   if key in {'result_array','reference_answers'} else r.get(key) for key in fields})
s=summary(rows,len(expected));s['timeout_count']=sum(r['outcome']=='timeout' for r in rows)
s['execution_success_percent']=100*s['execution_success']/len(rows)
s['scan_budget_failures']=sum('exceeding the configured limit' in (r.get('error') or '') for r in rows)
s['comparison_methods']={method:sum(r['comparison_method']==method for r in rows) for method in sorted({r['comparison_method'] for r in rows})}
s['grading_note']+=' One oversized array was reviewed in intact-row chunks. Two stalled tasks were terminated after a fresh retry exceeded five minutes and count as failures.'
Path('evaluation/array_summary.json').write_text(json.dumps(s,indent=2))
assert len(rows)==len(expected) and all(r['correct'] is not None for r in rows)
print(json.dumps(s,indent=2))
