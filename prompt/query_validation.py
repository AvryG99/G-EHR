"""Conservative checks for common generated BigQuery mistakes."""
import re
import sqlglot
from sqlglot import exp
from graph.tables import tables


def validate_revision_scope(sql, question):
    """Require explicit scoped predicates in every physical source of a revision.

    Deliberately conservative: revised CTEs must filter at the source, rather
    than relying on a later outer query to restore the requested scope.
    """
    scope = re.search(r'For patient subject_id\s*=\s*(\d+),\s*hospital admission hadm_id\s*=\s*(\d+):', question, re.I)
    if not scope:
        return
    expected = dict(zip(('subject_id', 'hadm_id'), scope.groups()))

    def guarantees(node):
        if isinstance(node, exp.Paren):
            return guarantees(node.this)
        if isinstance(node, exp.And):
            return guarantees(node.this) | guarantees(node.expression)
        if isinstance(node, exp.Or):
            return guarantees(node.this) & guarantees(node.expression)
        if isinstance(node, exp.EQ):
            for left, right in ((node.this, node.expression), (node.expression, node.this)):
                if isinstance(left, exp.Column) and isinstance(right, exp.Literal):
                    if left.name.lower() in expected and str(right.this) == expected[left.name.lower()]:
                        return {left.name.lower()}
        return set()

    from sqlglot.optimizer.scope import traverse_scope
    for selected in traverse_scope(sqlglot.parse_one(sql, read='bigquery')):
        if not isinstance(selected.expression, exp.Select):
            continue
        required = set()
        for source in selected.sources.values():
            if isinstance(source, exp.Table):
                required.update(set(expected) & tables.get(source.name.lower(), {}).get('attributes', {}).keys())
        if not required:
            continue
        where = selected.expression.args.get('where')
        guaranteed = guarantees(where.this) if where else set()
        if not required <= guaranteed:
            raise ValueError('Semantic revision must keep explicit requested patient/admission filters on every physical source branch, including CTEs and UNION branches.')


def validate_query(sql, question):
    tree = sqlglot.parse_one(sql, read='bigquery')
    for select in tree.find_all(exp.Select):
        if select.args.get('distinct') and select.args.get('order'):
            projected = {e.sql(dialect='bigquery').lower() for e in select.expressions}
            projected.update(e.alias.lower() for e in select.expressions if e.alias)
            for ordered in select.args['order'].expressions:
                value = ordered.this
                if isinstance(value, exp.Literal) or value.sql(dialect='bigquery').lower() in projected:
                    continue
                if any(isinstance(e, exp.Star) for e in select.expressions):
                    continue
                raise ValueError('SELECT DISTINCT requires ORDER BY expressions in the selected columns.')
    scope = re.search(r'For patient subject_id\s*=\s*(\d+),\s*hospital admission hadm_id\s*=\s*(\d+):', question, re.I)
    if not scope:
        return
    # Reuse the conservative, tested scope checker used by batch grading.
    from evaluation.scope_review import scope_violation
    if scope_violation(sql, *scope.groups()):
        raise ValueError('An OR branch escapes the requested patient/admission scope. Parenthesize OR predicates inside both ID filters.')
