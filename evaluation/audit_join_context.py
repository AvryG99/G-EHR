"""Compare multi-table generated SQL against logged initial RAG context."""
import csv
import json
from pathlib import Path
from collections import Counter
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from graph.tables import tables
from rag.clinical_semantics import normalize_clinical_entities


def run():
    mappings={m['title']:m for m in json.loads(Path('evaluation/note_mapping.json').read_text())}
    scopes={}
    for doc in json.loads(Path('test.final.json').read_text())['data']:
        m=mappings[doc['title']]
        for p in doc['paragraphs']:
            for qa in p['qas']:
                scopes[qa['id']]=normalize_clinical_entities(f"For patient subject_id = {m['subject_id']}, hospital admission hadm_id = {m['hadm_id']}: {qa['question']}")
    with Path('evaluation/notes_full_difficulty.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r['table_count'] and int(r['table_count'])>=2]
    requested={scopes[r['id']] for r in rows}
    prompts={}
    marker='Schema context after RAG (JSON; only these tables/columns are allowed):'
    for line in Path('logs/sql_prompts.jsonl').open():
        record=json.loads(line)
        if record.get('stage')!='sql_generation' or record['question'] not in requested:continue
        if marker not in record['prompt']:continue
        context=json.JSONDecoder().raw_decode(record['prompt'].split(marker,1)[1].lstrip())[0]
        prompts[record['question']]=(context,record['timestamp'])
    audit=[]
    for record in rows:
        matched=prompts.get(scopes[record['id']])
        if not matched:
            audit.append({'id':record['id'],'matched':False});continue
        ctx,timestamp=matched
        required=set(json.loads(record['tables']))
        missing_tables=sorted(required-set(ctx['tables']))
        missing_columns=set();unknown_columns=set();unchecked_columns=set();missing_joins=set();join_count=0
        tree=sqlglot.parse_one(record['sql'],read='bigquery')
        provided_joins=set()
        for text in ctx.get('joins',[]):
            for condition in text.split(' AND '):
                left,right=condition.split(' = ')
                provided_joins.add(frozenset((left,right)))
        for scope in traverse_scope(tree):
            physical={alias:source.name.lower() for alias,source in scope.sources.items() if isinstance(source,exp.Table)}
            for col in scope.columns:
                # Unqualified nested-subquery columns are propagated as external
                # references by sqlglot; do not assign them to the outer table.
                if col.find_ancestor(exp.Select) is not scope.expression:
                    continue
                if col.name=='*':continue
                if col.table:
                    candidates=[physical[col.table]] if col.table in physical else []
                else:
                    candidates=[t for t in physical.values() if col.name.lower() in tables.get(t,{}).get('attributes',{})]
                    if not candidates and len(physical)==1:candidates=list(physical.values())
                for table in candidates:
                    name=col.name.lower();ref=table+'.'+name
                    if name not in tables.get(table,{}).get('attributes',{}):unknown_columns.add(ref)
                    elif table in ctx['tables'] and name not in ctx['tables'][table]['columns']:missing_columns.add(ref)
            for join in scope.expression.args.get('joins',[]):
                pairs=[]
                on=join.args.get('on')
                if on:
                    for eq in on.find_all(exp.EQ):
                        l,r=eq.this,eq.expression
                        if isinstance(l,exp.Column) and isinstance(r,exp.Column) and l.table in physical and r.table in physical:
                            pairs.append((physical[l.table]+'.'+l.name.lower(),physical[r.table]+'.'+r.name.lower()))
                using=join.args.get('using') or []
                target=physical.get(join.this.alias_or_name)
                if using and target:
                    for identifier in using:
                        candidates=[t for alias,t in physical.items() if t!=target and identifier.name in tables.get(t,{}).get('attributes',{})]
                        if len(candidates)==1:pairs.append((candidates[0]+'.'+identifier.name,target+'.'+identifier.name))
                for pair in pairs:
                    join_count+=1
                    if frozenset(pair) not in provided_joins:missing_joins.add(' = '.join(pair))
        audit.append({'id':record['id'],'matched':True,'timestamp':timestamp,'question':record['question'],
            'sql_tables':sorted(required),'context_tables':sorted(ctx['tables']),
            'missing_tables':missing_tables,'missing_columns':sorted(missing_columns),
            'unknown_columns':sorted(unknown_columns),'missing_join_conditions':sorted(missing_joins),
            'checked_join_conditions':join_count,'correct':record['correct']=='True'})
    matched=[r for r in audit if r['matched']]
    sufficient=[r for r in matched if not any(r[k] for k in ('missing_tables','missing_columns','unknown_columns','missing_join_conditions'))]
    report={'multi_table_questions':len(rows),'matched_prompts':len(matched),
            'all_sql_tables_provided':sum(not r['missing_tables'] for r in matched),
            'missing_tables':sum(bool(r['missing_tables']) for r in matched),
            'missing_columns_with_tables_present':sum(bool(r['missing_columns']) for r in matched),
            'invalid_schema_columns':sum(bool(r['unknown_columns']) for r in matched),
            'join_conditions_absent_from_prompt':sum(bool(r['missing_join_conditions']) for r in matched),
            'context_supports_all_checked_references':len(sufficient),
            'explicit_join_queries':sum(r['checked_join_conditions']>0 for r in matched),
            'correct_with_supported_context':sum(r['correct'] for r in sufficient),
            'limitations':'Initial RAG prompt compared with final SQL (possibly repaired); multi-table SQL may use subqueries without JOIN. Counts overlap. Derived/correlated references and non-equality joins are not fully checked. This does not prove the generated query is the required correct query.',
            'details':audit}
    Path('evaluation/join_context_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))


if __name__=='__main__':run()
