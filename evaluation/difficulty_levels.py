"""Group evaluation by unique physical tables in generated SQL."""
import argparse
import csv
import json
from pathlib import Path
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope


def physical_tables(sql):
    if not sql:
        return [], 'missing_sql'
    try:
        statements=sqlglot.parse(sql,read='bigquery')
        if len(statements)!=1 or statements[0] is None:
            return [], 'invalid_statement_count'
        scopes=traverse_scope(statements[0])
        names=sorted({source.name.lower() for scope in scopes for source in scope.sources.values()
                      if isinstance(source,exp.Table) and source.name})
        return names, 'parsed' if names else 'no_physical_table'
    except sqlglot.errors.SqlglotError:
        return [], 'parse_error'


def analyze(prefix):
    source=json.loads(Path('test.final.json').read_text())
    questions={q['id']:q['question'] for d in source['data'] for p in d['paragraphs'] for q in p['qas']}
    per_question={}
    for line in Path(prefix+'_results.jsonl').open():
        record=json.loads(line)
        sql=record.get('executed_sql') or record.get('sql')
        names,status=physical_tables(sql)
        count=len(names)
        level=min(count,4) if count else None
        per_question[record['id']]={'id':record['id'],'question':record['question'],
            'level':level,'table_count':count if level else None,'tables':names,
            'classification_status':status,'correct':record['correct'],
            'execution_success':record['execution_success'],'sql':sql}
    for qid,question in questions.items():
        per_question.setdefault(qid,{'id':qid,'question':question,'level':None,'table_count':None,
            'tables':[],'classification_status':'not_completed','correct':None,'execution_success':None,'sql':None})
    levels=[]
    classified=sum(r['level'] is not None for r in per_question.values())
    for level in range(1,5):
        rows=[r for r in per_question.values() if r['level']==level]
        scored=[r for r in rows if r['correct'] is not None]
        correct=sum(r['correct'] is True for r in rows)
        levels.append({'level':level,'table_rule':str(level) if level<4 else '4+',
            'questions':len(rows),'dataset_percentage':100*len(rows)/len(questions),
            'classified_percentage':100*len(rows)/classified if classified else None,
            'scored':len(scored),'correct':correct,'unscored':len(rows)-len(scored),
            'accuracy_scored_percent':100*correct/len(scored) if scored else None,
            'correct_all_level_percent':100*correct/len(rows) if rows else None})
    report={'total_questions':len(questions),'classified':classified,'unclassified':len(questions)-classified,
        'method':'Unique physical table names in generated SQL, including subqueries; CTE aliases and repeated self-joins do not add tables. This is generated-query complexity, not minimum required tables.',
        'accuracy_denominator':'Scored questions within each level. SQL execution failures with a verdict remain in the denominator; unscored comparisons are excluded.',
        'levels':levels,
        'unclassified_ids':[{'id':r['id'],'reason':r['classification_status']} for r in per_question.values() if r['level'] is None]}
    Path(prefix+'_difficulty_summary.json').write_text(json.dumps(report,indent=2))
    with Path(prefix+'_difficulty.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['id','question','level','table_count','tables','classification_status','correct','execution_success','sql']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for qid in questions:
            row=dict(per_question[qid]);row['tables']=json.dumps(row['tables']);writer.writerow(row)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-prefix',default='evaluation/notes_full')
    analyze(parser.parse_args().output_prefix)
