"""Compact, schema-grounded context for retrieved columns and join bridges."""
import json
from graph.tables import tables
from graph.graph_builder import describe_join_paths

# Operational columns needed to identify, filter and interpret retrieved values.
SUPPORT_COLUMNS = {
    'noteevents': ('row_id', 'subject_id', 'hadm_id', 'chartdate', 'category', 'text'),
    'patients': ('subject_id',),
    'admissions': ('subject_id', 'hadm_id', 'admittime'),
    'icustays': ('subject_id', 'hadm_id', 'icustay_id', 'intime'),
    'prescriptions': ('drug', 'prod_strength'),
    'labevents': ('subject_id', 'hadm_id', 'itemid', 'charttime', 'value', 'valuenum', 'valueuom'),
    'chartevents': ('subject_id', 'hadm_id', 'icustay_id', 'itemid', 'charttime', 'value', 'valuenum', 'valueuom'),
    'd_labitems': ('itemid', 'label'),
    'd_items': ('itemid', 'label', 'linksto'),
    'd_icd_diagnoses': ('icd9_code', 'short_title', 'long_title'),
    'd_icd_procedures': ('icd9_code', 'short_title', 'long_title'),
    'diagnoses_icd': ('icd9_code', 'seq_num'),
    'procedures_icd': ('icd9_code', 'seq_num'),
}


def select_schema_columns(table_info):
    """Keep retrieved columns and join/filter support, preserving RAG scores."""
    selected = {}
    for table, info in table_info.items():
        if table not in tables:
            continue
        selected[table] = {
            'total_score': info.get('total_score', 0),
            'role': info.get('role', 'retrieved'),
            'columns': [dict(col) for col in info.get('columns', [])
                        if col['name'] in tables[table]['attributes']],
        }
    # Dictionary closure follows actual FK definitions; never equate item IDs
    # between the laboratory and bedside dictionaries.
    for table in list(selected):
        for foreign_key in tables[table]['foreign_keys']:
            lookup = foreign_key['table']
            if lookup.startswith('d_'):
                selected.setdefault(lookup, {'columns': [], 'total_score': 0, 'role': 'dictionary'})
    paths = describe_join_paths(selected)
    required = {}
    for path in paths:
        for join in path['joins']:
            for side in ('left', 'right'):
                table = join[side]
                selected.setdefault(table, {'columns': [], 'total_score': 0, 'role': 'join_bridge'})
                required.setdefault(table, set()).add(join.get(side+'_key', join['key']))
    for table, info in selected.items():
        attributes = tables[table]['attributes']
        names = set(SUPPORT_COLUMNS.get(table, ())) | required.get(table, set())
        for fk in tables[table]['foreign_keys']:
            if fk['table'] in selected:
                names.add(fk['column'])
        if len(selected) > 1:
            names.update(name for name in ('subject_id', 'hadm_id', 'icustay_id') if name in attributes)
        if 'itemid' in attributes:
            names.add('itemid')
            names.update(name for name in ('label', 'valueuom', 'charttime', 'starttime', 'endtime') if name in attributes)
        existing = {col['name']: col for col in info['columns']}
        for name in sorted(names & attributes.keys()):
            existing.setdefault(name, {'name': name, 'score': 0})
        info['columns'] = [
            dict(col, description=attributes[name]['description'], datatype=attributes[name]['datatype'])
            for name, col in existing.items()
        ]
    return selected


def build_schema_context(rag, feasible_values=None):
    selected = select_schema_columns(rag.get('tables_info', {}))
    paths = describe_join_paths(selected)
    joins = sorted({f"{join['left']}.{join.get('left_key', join['key'])} = {join['right']}.{join.get('right_key', join['key'])}"
                    for path in paths for join in path['joins']})
    for child in selected:
        for fk in tables[child]['foreign_keys']:
            if fk['table'] in selected:
                joins.append(f"{fk['table']}.{fk['references']} = {child}.{fk['column']}")
    for index, left in enumerate(sorted(selected)):
        for right in sorted(selected)[index+1:]:
            if all(key in tables[left]['attributes'] and key in tables[right]['attributes']
                   for key in ('subject_id', 'hadm_id')):
                joins.append(f"{left}.subject_id = {right}.subject_id AND {left}.hadm_id = {right}.hadm_id")
    joins = sorted(set(joins))
    context = {'database': 'MIMIC-III original', 'dialect': 'BigQuery GoogleSQL', 'tables': {}, 'joins': joins}
    for table, info in selected.items():
        schema = tables[table]
        context['tables'][table] = {
            'role': info.get('role', 'retrieved'),
            'meaning': ('Medication orders; does not confirm administration.'
                        if table == 'prescriptions' else schema['description']),
            'columns': {
                col['name']: {'type': col['datatype'], 'meaning': col['description'],
                              'nullable': schema['attributes'][col['name']]['nullable']}
                for col in info['columns']
            },
        }
    context['source_guidance'] = 'Prioritize query_anchor and narrative_evidence sources; dictionary tables resolve labels/codes, and join_bridge tables provide keys. Supplemental retrieved tables need not be joined unless required by the question.'
    context['join_guidance'] = 'Shared subject_id/hadm_id conditions join records at admission grain; filter or aggregate event tables before joining to avoid multiplying rows. These shared-entity joins are not declared foreign keys.'
    context['lookup_values'] = [value for value in feasible_values or []
                                if value.get('table') in context['tables']
                                and value.get('column') in context['tables'][value['table']]['columns']]
    return context


def format_schema_context(rag, feasible_values=None):
    return json.dumps(build_schema_context(rag, feasible_values), ensure_ascii=False, separators=(',', ':'))
