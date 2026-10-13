"""Replay new context rules on logged RAG output; no SQL/model execution."""
import json
from pathlib import Path
from rag.query_context import apply_query_context
from prompt.schema_context import build_schema_context
from prompt.schema_validation import validate_schema_context
from rag.clinical_semantics import normalize_clinical_entities


def run():
    audit=json.loads(Path('evaluation/join_context_audit.json').read_text())['details']
    mappings={m['title']:m for m in json.loads(Path('evaluation/note_mapping.json').read_text())}
    questions={}
    for doc in json.loads(Path('test.final.json').read_text())['data']:
        m=mappings[doc['title']]
        for p in doc['paragraphs']:
            for qa in p['qas']:
                questions[qa['id']]=(qa['question'],normalize_clinical_entities(f"For patient subject_id = {m['subject_id']}, hospital admission hadm_id = {m['hadm_id']}: {qa['question']}"))
    prompts={};marker='Schema context after RAG (JSON; only these tables/columns are allowed):'
    for line in Path('logs/sql_prompts.jsonl').open():
        r=json.loads(line)
        if r['stage']=='sql_generation' and marker in r['prompt']:
            prompts[r['question']]=json.JSONDecoder().raw_decode(r['prompt'].split(marker,1)[1].lstrip())[0]
    details=[]
    for row in audit:
        question,scoped=questions[row['id']]
        original=prompts[scoped]
        table_info={table:{'columns':[{'name':column,'score':0} for column in info['columns']]} for table,info in original['tables'].items()}
        updated=build_schema_context({'tables_info':apply_query_context(normalize_clinical_entities(question),table_info)})
        missing=sorted(set(row['sql_tables'])-set(updated['tables']))
        details.append({'id':row['id'],'question':question,'previous_missing_tables':row['missing_tables'],
                        'updated_missing_tables':missing,'updated_tables':sorted(updated['tables'])})
    previously_missing=[d for d in details if d['previous_missing_tables']]
    report={'questions':len(details),'old_all_tables_covered':sum(not d['previous_missing_tables'] for d in details),
            'updated_all_tables_covered':sum(not d['updated_missing_tables'] for d in details),
            'previously_missing_fixed':sum(not d['updated_missing_tables'] for d in previously_missing),
            'previously_missing_total':len(previously_missing),
            'method':'Offline replay of current context expansion over logged selected schema; compares to old generated SQL, not required-query ground truth or answer accuracy.',
            'details':details}
    Path('evaluation/join_context_replay.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))


if __name__=='__main__':run()
