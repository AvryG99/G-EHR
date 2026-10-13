"""Keep evaluation scoping identifiers out of semantic retrieval."""
import re


def retrieval_question(question):
    return re.sub(
        r'^For patient subject_id\s*=\s*\d+,\s*hospital admission hadm_id\s*=\s*\d+:\s*',
        '', question, flags=re.IGNORECASE,
    )


def preferred_tables(query):
    q = query.lower()
    if re.search(r'\b(birth|born|dob|gender|sex)\b', q):
        return {'patients'}
    if re.search(r'\b(history|symptoms?|complaints?|exacerbation|considered|suffer|suffering)\b', q):
        return {'noteevents'}
    return set()


STRUCTURED_REQUEST = re.compile(
    r'\b(?:icd(?:9|10)?|cpt|itemid|lab(?:oratory)?|labevents|'
    r'hemoglobin|creatinine|glucose|sodium|potassium|lactate|'
    r'heart rate|blood pressure|temperature|oxygen saturation|'
    r'dose|dosage|route|strength|prescriptions?|prescribed|'
    r'admission date|discharge date|length of stay|duration|'
    r'how many|average|median|minimum|maximum)\b', re.IGNORECASE,
)
NARRATIVE_REQUEST = re.compile(
    r'\b(?:history|symptoms?|complaints?|exacerbation|considered|'
    r'suffer(?:ing)?|mentions?|mentioned|records?|notes?|reports?|'
    r'status|controlled|control|why|findings?)\b|'
    r'\b(?:does|did|has|had|is|was)\b.*\bpatient\b', re.IGNORECASE,
)


# Domain anchors supplement dense retrieval without depending on benchmark answers.
DOMAIN_RULES = (
    (r"\b(labs?|laboratory|lab results?|lactate|lactic acid|creatinine|glucose|sodium|potassium|hemoglobin|haemoglobin|hematocrit|haematocrit|hct|wbc|platelets?|troponin|ck|cpk|bun|hypernatremia|hyponatremia)\b", "labevents", ("subject_id", "hadm_id", "itemid", "charttime", "value", "valuenum", "valueuom", "flag")),
    (r"\b(heart rate|blood pressure|sbp|dbp|systolic blood pressure|diastolic blood pressure|temperature|spo2|oxygen saturation|respiratory rate|vital signs?)\b", "chartevents", ("subject_id", "hadm_id", "icustay_id", "itemid", "charttime", "value", "valuenum", "valueuom")),
    (r"\b(prescribed|prescriptions?|dosage|dose|route|drug strength|medication orders?)\b", "prescriptions", ("subject_id", "hadm_id", "drug", "prod_strength", "route", "dose_val_rx", "dose_unit_rx", "startdate", "enddate")),
    (r"\b(procedure duration|procedure start|procedure end|incision)\b", "procedureevents_mv", ("subject_id", "hadm_id", "icustay_id", "itemid", "starttime", "endtime", "value", "valueuom")),
    (r"\b(icd(?:-?9)?|diagnosis codes?|coded diagnoses)\b", "diagnoses_icd", ("subject_id", "hadm_id", "icd9_code", "seq_num")),
    (r"\b(icu|intensive care|careunit)\b", "icustays", ("subject_id", "hadm_id", "icustay_id", "intime", "outtime", "los")),
    (r"\b(age|aged)\b", "patients", ("subject_id", "dob")),
    (r"\b(age|aged)\b", "admissions", ("subject_id", "hadm_id", "admittime")),
    (r"\b(admission date|admission time|admitted|discharge date|discharge time|(?:last|latest|first|previous|prior) (?:hospital )?admission|before admission|after admission)\b", "admissions", ("subject_id", "hadm_id", "admittime", "dischtime")),
)


def structured_context(query):
    return {table: {'columns': [{'name': name, 'score': 1.0} for name in names], 'total_score': 1.0}
            for pattern, table, names in DOMAIN_RULES if re.search(pattern, query, re.IGNORECASE)}


def apply_query_context(query, table_info):
    """Combine domain-specific schema with clinical narrative evidence."""
    anchors = structured_context(query)
    preferred = preferred_tables(query)
    selected = {table: dict(info, columns=[dict(c) for c in info.get('columns', [])])
                for table, info in table_info.items()}
    if preferred == {'patients'}:
        target = 'dob' if re.search(r'\b(birth|born|dob)\b', query, re.IGNORECASE) else 'gender'
        selected = {'patients': {'columns': [{'name': target, 'score': 1.0}], 'total_score': 1.0}}
        if not anchors:
            return selected
    narrative = bool(NARRATIVE_REQUEST.search(query)) or preferred == {'noteevents'}
    # Preserve dense candidates for mixed/multi-table questions. Domain anchors
    # and narrative roles guide priority without deleting possible join partners.
    for table, info in anchors.items():
        current = selected.setdefault(table, {'columns': [], 'total_score': 1.0})
        columns = {c['name']: c for c in current['columns']}
        for col in info['columns']:
            columns.setdefault(col['name'], col)
        current['columns'] = list(columns.values())
        current['role'] = 'query_anchor'
    use_notes = narrative or (preferred != {'patients'} and not anchors and not STRUCTURED_REQUEST.search(query))
    if use_notes:
        # A narrative-only request does not need unrelated dense hits. Keep
        # domain anchors for genuinely mixed requests (e.g. history + labs).
        if not anchors and not STRUCTURED_REQUEST.search(query):
            selected = {}
        selected['noteevents'] = {
            'columns': [{'name': name, 'score': 1.0} for name in
                        ('row_id', 'subject_id', 'hadm_id', 'chartdate', 'category', 'text')],
            'total_score': 1.0, 'role': 'narrative_evidence',
        }
    return selected
