# graph_builder.py
import networkx as nx
from .tables import tables

def build_schema_graph():
    G = nx.DiGraph()

    # =====================
    # Add table nodes
    # =====================
    for table_name in tables.keys():
        G.add_node(table_name)

    # =====================
    # Core entity relations
    # =====================
    G.add_edge("patients", "admissions", key="subject_id")
    G.add_edge("patients", "icustays", key="subject_id")

    G.add_edge("admissions", "icustays", key="hadm_id")

    # =====================
    # Admission-level tables
    # =====================
    G.add_edge("admissions", "diagnoses_icd", key="hadm_id")
    G.add_edge("admissions", "procedures_icd", key="hadm_id")
    G.add_edge("admissions", "prescriptions", key="hadm_id")
    G.add_edge("admissions", "labevents", key="hadm_id")
    G.add_edge("admissions", "microbiologyevents", key="hadm_id")
    G.add_edge("admissions", "transfers", key="hadm_id")

    # =====================
    # ICU stay–level tables
    # =====================
    G.add_edge("icustays", "chartevents", key="icustay_id")
    G.add_edge("icustays", "inputevents_cv", key="icustay_id")
    G.add_edge("icustays", "outputevents", key="icustay_id")
    G.add_edge("icustays", "transfers", key="icustay_id")

    # =====================
    # Dictionary / lookup tables
    # =====================
    G.add_edge("diagnoses_icd", "d_icd_diagnoses", key="icd9_code")
    G.add_edge("procedures_icd", "d_icd_procedures", key="icd9_code")

    G.add_edge("chartevents", "d_items", key="itemid")
    G.add_edge("inputevents_cv", "d_items", key="itemid")
    G.add_edge("outputevents", "d_items", key="itemid")

    G.add_edge("labevents", "d_labitems", key="itemid")

    return G


def describe_join_paths(table_names):
    """Return valid shortest join paths and keys between candidate tables."""
    graph = build_schema_graph()
    undirected = graph.to_undirected()
    candidates = sorted(set(table_names) & set(graph.nodes))
    paths = []

    for index, source in enumerate(candidates):
        for target in candidates[index + 1:]:
            try:
                nodes = nx.shortest_path(undirected, source, target)
            except nx.NetworkXNoPath:
                continue

            joins = []
            for left, right in zip(nodes, nodes[1:]):
                edge = graph.get_edge_data(left, right)
                if edge is None:
                    edge = graph.get_edge_data(right, left)
                joins.append({"left": left, "right": right, "key": edge["key"]})
            paths.append({"source": source, "target": target, "joins": joins})

    return paths
