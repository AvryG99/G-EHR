"""Identify provable patient/admission leaks in simple notes WHERE clauses."""
import argparse
import json
from pathlib import Path
import sqlglot
from sqlglot import exp


def scope_violation(sql, subject_id, hadm_id):
    try:
        tree=sqlglot.parse_one(sql,read='bigquery')
    except Exception:
        return False
    # Review only unambiguous single-table queries, without outer CTE filters.
    if not isinstance(tree,exp.Select) or tree.args.get('with_') or tree.args.get('joins'):
        return False
    from_clause=tree.args.get('from_')
    table=from_clause.this if from_clause else None
    if not isinstance(table,exp.Table) or table.name.lower()!='noteevents':return False
    where=tree.args.get('where')
    if not where or not where.find(exp.Or):return False
    expected={'subject_id':str(subject_id),'hadm_id':str(hadm_id)}

    def guarantees(node):
        if isinstance(node,exp.Paren):return guarantees(node.this)
        if isinstance(node,exp.And):return guarantees(node.this)|guarantees(node.expression)
        if isinstance(node,exp.Or):return guarantees(node.this)&guarantees(node.expression)
        if isinstance(node,exp.EQ):
            for left,right in ((node.this,node.expression),(node.expression,node.this)):
                if isinstance(left,exp.Column) and isinstance(right,exp.Literal):
                    name=left.name.lower()
                    if name in expected and str(right.this)==expected[name]:return {name}
        return set()
    referenced={c.name.lower() for c in where.find_all(exp.Column)}
    # Omitted scopes and complex relational cases require separate review.
    if not set(expected)<=referenced:return False
    return not set(expected)<=guarantees(where.this)


def review(prefix):
    reviews=[]
    for line in Path(prefix+'_results.jsonl').open():
        record=json.loads(line)
        if record['execution_success'] and scope_violation(record.get('executed_sql') or record.get('sql') or '',record['subject_id'],record['hadm_id']):
            reviews.append({'id':record['id'],'correct':False,
                'comparison_method':'verified_sql_scope_violation',
                'comparison_reason':'SQL AND/OR precedence leaves at least one WHERE branch without the requested patient/admission filters. The query does not enforce the requested scope.'})
    path=Path(prefix+'_comparison_reviews.json')
    existing=json.loads(path.read_text()) if path.exists() else []
    merged={r['id']:r for r in existing}
    merged.update({r['id']:r for r in reviews})
    path.write_text(json.dumps(list(merged.values()),indent=2))
    print('Provable SQL scope violations:',len(reviews))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-prefix',required=True)
    review(parser.parse_args().output_prefix)
