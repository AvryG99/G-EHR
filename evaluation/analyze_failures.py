import csv
import json
import re
from collections import Counter
from pathlib import Path
from rag.clinical_semantics import normalize_clinical_entities

rows=[json.loads(line) for line in Path('evaluation/array_results.jsonl').read_text().splitlines()]
counts=Counter(); details=[];budget=[]
for r in rows:
 if r['execution_success']:
  category='correct' if r['correct'] else 'empty_result' if not r['result_array'] else 'wrong_nonempty_result'
 else:
  error=r.get('error') or ''
  m=re.search(r'process (\d+) bytes.*limit of (\d+) bytes',error)
  if m:
   category='scan_budget';budget.append({'id':r['id'],'estimated_bytes':int(m[1]),'configured_limit':int(m[2])})
  elif 'timed out' in error:category='timeout'
  elif 'Connection error' in error:category='connection'
  elif 'Syntax error' in error or 'Required keyword' in error:category='syntax'
  elif 'not found inside' in error or 'Unrecognized name' in error:category='unknown_column_or_alias'
  elif 'Undeclared parameter' in error:category='unbound_parameter'
  elif 'No matching signature' in error:category='type_mismatch'
  elif 'LEFT SEMI JOIN' in error:category='invalid_join'
  else:category='other_execution_error'
 counts[category]+=1;details.append(dict(id=r['id'],category=category,question=r['question'],error=r.get('error','')))
# Observe context availability; do not claim this alone establishes causation.
prompts={}
for line in Path('logs/sql_prompts.jsonl').read_text().splitlines():
 r=json.loads(line)
 if r.get('stage')=='sql_generation':prompts[r['question']]=r['prompt']
coverage=Counter();syntax_examples=[]
marker='Schema context after RAG (JSON; only these tables/columns are allowed):'
for r in rows:
 if r['correct']:continue
 scoped=f"For patient subject_id = {r['subject_id']}, hospital admission hadm_id = {r['hadm_id']}: {r['question']}"
 prompt=prompts.get(normalize_clinical_entities(scoped))
 if not prompt or marker not in prompt:coverage['prompt_not_matched']+=1;continue
 context=json.JSONDecoder().raw_decode(prompt.split(marker,1)[1].lstrip())[0]
 has_notes='text' in context.get('tables',{}).get('noteevents',{}).get('columns',{})
 coverage['note_text_available' if has_notes else 'note_text_absent']+=1
 if r['id'] in {'262','436','642','1062','259','564','918'}:
  syntax_examples.append({'id':r['id'],'schema_tables':list(context['tables']),'note_text_available':has_notes,'sql':r['sql']})
report={'counts':dict(counts),'incorrect_total':sum(not r['correct'] for r in rows),
        'failed_question_context_observations':dict(coverage),
        'root_cause_note':'Absence of notes context is an observed coverage gap for a note-QA benchmark, not proof that RAG alone caused every failure. Wrong nonempty results need per-question review for RAG versus LLM logic.',
        'budget_failures':sorted(budget,key=lambda x:x['estimated_bytes']),
        'maximum_estimated_bytes':max(x['estimated_bytes'] for x in budget),
        'budget_by_current_limit':{str(limit):{'count':sum(x['configured_limit']==limit for x in budget),'maximum_estimated_bytes':max(x['estimated_bytes'] for x in budget if x['configured_limit']==limit)} for limit in {x['configured_limit'] for x in budget}},
        'illustrative_failures':syntax_examples}
Path('evaluation/failure_analysis.json').write_text(json.dumps(report,indent=2))
with Path('evaluation/failure_categories.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=['id','category','question','error']);writer.writeheader();writer.writerows(details)
print(json.dumps({k:v for k,v in report.items() if k not in {'budget_failures','illustrative_failures'}},indent=2))
