"""Reject tables and resolvable columns absent from the supplied RAG context."""
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from prompt.schema_context import build_schema_context


def validate_schema_context(sql, rag):
    context = build_schema_context(rag)['tables']
    tree = sqlglot.parse_one(sql, read='bigquery')
    for scope in traverse_scope(tree):
        physical = {alias: source.name.lower() for alias, source in scope.sources.items()
                    if isinstance(source, exp.Table)}
        for table in physical.values():
            if table not in context:
                raise ValueError(f"RAG context does not allow table {table}. Use only supplied tables.")
        for col in scope.columns:
            if col.name == '*' or col.find_ancestor(exp.Select) is not scope.expression:
                continue
            if col.table:
                table = physical.get(col.table)
                if table and col.name.lower() not in context[table]['columns']:
                    raise ValueError(f"RAG context does not allow column {table}.{col.name}.")
            elif len(physical) == 1 and all(isinstance(s, exp.Table) for s in scope.sources.values()):
                table = next(iter(physical.values()))
                if col.name.lower() not in context[table]['columns']:
                    # Correlated subqueries may resolve unqualified columns outside.
                    parent = scope.parent
                    outer = False
                    while parent:
                        for source in parent.sources.values():
                            if isinstance(source, exp.Table) and col.name.lower() in context.get(source.name.lower(), {}).get('columns', {}):
                                outer = True
                        parent = parent.parent
                    if not outer:
                        raise ValueError(f"RAG context does not allow column {table}.{col.name}.")
