"""Shared guidance for querying the original MIMIC-III data."""
ORIGINAL_SCHEMA_RULES = """
- This is original MIMIC-III, not a cleaned or derived dataset.
- There is no cost table or admissions.age column. Compute age at admission
  from patients.dob and admissions.admittime; ages over 89 are deidentified.
- diagnoses_icd and procedures_icd have seq_num, not charttime; seq_num = 1
  identifies the primary code. ICD-9 codes are strings; preserve leading zeros
  and use stored codes without inserting decimal points.
- Time columns are timestamps, not Unix epochs. Use the SQL dialect's timestamp
  arithmetic. Shifted dates do not represent real calendar dates.
- CareVue inputevents_cv uses charttime; MetaVision inputevents_mv and
  procedureevents_mv use starttime/endtime. Consult both input systems when
  the question concerns all administrations. Prescriptions describe orders.
- BigQuery billing limits are API job configuration, never SQL OPTION clauses.
  LIMIT and itemid filtering do not ensure reduced bytes scanned.
- Clinical symptoms, history, and narrative findings belong in noteevents.text.
  Do not search d_items for disease names or infer symptoms from valueuom.
- For narrative questions, use noteevents.text as clinical evidence, preserve
  negation and distinguish current findings from prior history. A mention count
  is not a count of episodes or proof of disease. Keep requested patient/admission
  filters on every UNION branch and return relevant text excerpts when needed.
- Missing rows or COUNT = 0 do not establish clinical absence.
- For narrative questions return relevant noteevents.text evidence, including
  negated mentions; do not replace evidence with CASE/COUNT-derived Yes/No.
  Do not decide clinical presence from a single arbitrary note with LIMIT 1.
  Use LIMIT 1 only when the question explicitly requests a single latest/first
  record, with a deterministic chronological order and row_id tie-breaker.
- Filter noteevents directly by its subject_id/hadm_id. Join admissions only
  if admission attributes are requested. Do not invent category/description
  filters: use them only when requested or supported by supplied lookup values.
  A narrative status question does not implicitly request the latest note.
- Parenthesize every OR group combined with patient/admission filters.
- With SELECT DISTINCT, every ORDER BY expression must appear in the SELECT
  list; otherwise remove DISTINCT or use a subquery at the intended grain.
- Query chartevents, never its physical chartevents_1 through _14 partitions.
- Join patients by subject_id, admissions by hadm_id, and icustays by icustay_id.
  row_id identifies a row within its own table and is not a cross-table join key.
- Use d_labitems for labevents and d_items for other item-based events.
- Nullable hadm_id/icustay_id do not imply a missing patient. Choose join type
  and aggregation grain carefully; joining event tables can multiply rows.
- Examples are guidance only; the allowed original schema takes precedence.
"""
