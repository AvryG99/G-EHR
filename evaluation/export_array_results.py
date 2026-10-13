"""Validate, apply completed comparison reviews, and export a full-run CSV."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from evaluation.run_array_batch import FIELDS, summary


def export(prefix):
    path=Path(prefix+'_results.jsonl')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    source=json.loads(Path('test.final.json').read_text())
    ids=[q['id'] for doc in source['data'] for p in doc['paragraphs'] for q in p['qas']]
    assert len(rows)==len(ids) and {r['id'] for r in rows}==set(ids), 'Incomplete or duplicate results'
    review_path=Path(prefix+'_comparison_reviews.json')
    reviews={r['id']:r for r in json.loads(review_path.read_text())} if review_path.exists() else {}
    for row in rows:
        if row['id'] in reviews:
            row['original_correct']=row['correct']
            row['original_comparison_reason']=row.get('comparison_reason')
            row['original_comparison_error']=row.pop('comparison_error',None)
            row.update(reviews[row['id']])
        row.setdefault('comparison_method', 'model_semantic' if row['execution_success'] else 'execution_failure')
        if 'timed out' in (row.get('error') or '').lower():
            row['outcome']='timeout'
        else:
            row['outcome']='unscored' if row['correct'] is None else 'correct' if row['correct'] else 'incorrect' if row['execution_success'] else 'execution_error'
    order={value:index for index,value in enumerate(ids)}
    rows.sort(key=lambda r:order[r['id']])
    temporary=path.with_suffix('.tmp')
    temporary.write_text(''.join(json.dumps(r,ensure_ascii=False,default=str)+'\n' for r in rows))
    temporary.replace(path)
    with Path(prefix+'_results.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        fields=list(dict.fromkeys(FIELDS+['comparison_method','outcome','original_correct','original_comparison_reason']))
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in rows:
            writer.writerow({key:json.dumps(row.get(key),ensure_ascii=False,default=str)
                             if key in {'result_array','reference_answers','review_history'} else row.get(key) for key in fields})
    report=summary(rows,len(ids))
    report.update(timeout_count=sum(r['outcome']=='timeout' for r in rows),
                  scan_budget_failures=sum('exceeding the configured limit' in (r.get('error') or '') for r in rows),
                  execution_success_percent=100*sum(r['execution_success'] for r in rows)/len(rows),
                  empty_results=sum(r['execution_success'] and not r['result_array'] for r in rows),
                  comparison_methods=dict(Counter(r['comparison_method'] for r in rows)),
                  accuracy_scored_percent=100*report['correct']/(len(rows)-report['unscored']) if len(rows)>report['unscored'] else None)
    if report['comparison_methods'].get('verified_sql_scope_violation', 0):
        report['method'] += ' Includes deterministic SQL patient/admission scope checks.'
        report['grading_note'] += ' Queries with provably unscoped OR branches count as incorrect even if a model could find a reference span somewhere in the returned array.'
    Path(prefix+'_summary.json').write_text(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-prefix',required=True)
    print(json.dumps(export(parser.parse_args().output_prefix),indent=2))
