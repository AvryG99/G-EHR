# graph_builder.py
import networkx as nx
from .tables import tables
def build_schema_graph():
    G = nx.DiGraph()

    # Add nodes
    for table_name, schema in tables.items():
        G.add_node(
            table_name,
            metadata={
                "table": table_name,
                "primary_key": schema["primary_key"],
                "description": schema["description"]
            },
            attributes=schema["attributes"]
        )

    # Add relationships (hardcoded demo — sau này có thể lấy từ DB)
    # Patients ↔ Admissions/ICU
    G.add_edge("patients", "admissions", relation="subject_id")
    G.add_edge("patients", "icustays", relation="subject_id")

    # Admissions ↔ ICU stays
    G.add_edge("admissions", "icustays", relation="hadm_id")

    # Admissions ↔ Other hospital info
    G.add_edge("admissions", "callout", relation="hadm_id")
    G.add_edge("admissions", "services", relation="hadm_id")
    G.add_edge("admissions", "diagnoses_icd", relation="hadm_id")
    G.add_edge("admissions", "drgcodes", relation="hadm_id")
    G.add_edge("admissions", "procedures_icd", relation="hadm_id")
    G.add_edge("admissions", "cptevents", relation="hadm_id")

    # ICU stays ↔ Events inside ICU
    G.add_edge("icustays", "chartevents", relation="icustay_id")
    G.add_edge("icustays", "datetimeevents", relation="icustay_id")
    G.add_edge("icustays", "inputevents_cv", relation="icustay_id")
    G.add_edge("icustays", "inputevents_mv", relation="icustay_id")
    G.add_edge("icustays", "outputevents", relation="icustay_id")
    G.add_edge("icustays", "procedureevents_mv", relation="icustay_id")
    G.add_edge("icustays", "noteevents", relation="icustay_id")

    # Patients ↔ Event tables (some skip admissions)
    G.add_edge("patients", "chartevents", relation="subject_id")
    G.add_edge("patients", "datetimeevents", relation="subject_id")
    G.add_edge("patients", "inputevents_cv", relation="subject_id")
    G.add_edge("patients", "inputevents_mv", relation="subject_id")
    G.add_edge("patients", "outputevents", relation="subject_id")
    G.add_edge("patients", "procedureevents_mv", relation="subject_id")
    G.add_edge("patients", "noteevents", relation="subject_id")
    G.add_edge("patients", "prescriptions", relation="subject_id")
    G.add_edge("patients", "labevents", relation="subject_id")
    G.add_edge("patients", "microbiologyevents", relation="subject_id")

    # Admissions ↔ Prescriptions, Labs, Micro
    G.add_edge("admissions", "prescriptions", relation="hadm_id")
    G.add_edge("admissions", "labevents", relation="hadm_id")
    G.add_edge("admissions", "microbiologyevents", relation="hadm_id")

    # Dictionary tables ↔ Event tables
    G.add_edge("d_items", "chartevents", relation="itemid")
    G.add_edge("d_items", "datetimeevents", relation="itemid")
    G.add_edge("d_items", "outputevents", relation="itemid")

    G.add_edge("d_labitems", "labevents", relation="itemid")

    G.add_edge("d_cpt", "cptevents", relation="cpt_cd")

    G.add_edge("d_icd_diagnoses", "diagnoses_icd", relation="icd9_code")
    G.add_edge("d_icd_procedures", "procedures_icd", relation="icd9_code")

    # print(G)
    return G


build_schema_graph()