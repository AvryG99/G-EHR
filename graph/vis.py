# vis.py
import matplotlib
matplotlib.use("Agg")  # Headless backend, không cần GUI
import matplotlib.pyplot as plt
import networkx as nx

# =====================
# Tables (tương tự tables.py)
# =====================
tables = {
    "patients": {},
    "admissions": {},
    "icustays": {},
    "diagnoses_icd": {},
    "procedures_icd": {},
    "prescriptions": {},
    "labevents": {},
    "chartevents": {},
    "inputevents_cv": {},
    "outputevents": {},
    "microbiologyevents": {},
    "transfers": {},
    "d_items": {},
    "d_labitems": {},
    "d_icd_diagnoses": {},
    "d_icd_procedures": {},
}

# =====================
# Build schema graph
# =====================
def build_schema_graph():
    G = nx.DiGraph()
    # Add nodes
    for table_name in tables.keys():
        G.add_node(table_name)

    # Core entity relations
    G.add_edge("patients", "admissions", key="subject_id")
    G.add_edge("patients", "icustays", key="subject_id")
    G.add_edge("admissions", "icustays", key="hadm_id")

    # Admission-level tables
    G.add_edge("admissions", "diagnoses_icd", key="hadm_id")
    G.add_edge("admissions", "procedures_icd", key="hadm_id")
    G.add_edge("admissions", "prescriptions", key="hadm_id")
    G.add_edge("admissions", "labevents", key="hadm_id")
    G.add_edge("admissions", "microbiologyevents", key="hadm_id")
    G.add_edge("admissions", "transfers", key="hadm_id")

    # ICU-level tables
    G.add_edge("icustays", "chartevents", key="icustay_id")
    G.add_edge("icustays", "inputevents_cv", key="icustay_id")
    G.add_edge("icustays", "outputevents", key="icustay_id")
    G.add_edge("icustays", "transfers", key="icustay_id")

    # Dictionary / lookup tables
    G.add_edge("diagnoses_icd", "d_icd_diagnoses", key="icd9_code")
    G.add_edge("procedures_icd", "d_icd_procedures", key="icd9_code")

    G.add_edge("chartevents", "d_items", key="itemid")
    G.add_edge("inputevents_cv", "d_items", key="itemid")
    G.add_edge("outputevents", "d_items", key="itemid")
    G.add_edge("labevents", "d_labitems", key="itemid")

    return G

# =====================
# Layered layout (EHR style)
# =====================
def layered_layout():
    layers = {
        "patients": 5,
        "admissions": 4,
        "icustays": 3,
        "diagnoses_icd": 2,
        "procedures_icd": 2,
        "prescriptions": 2,
        "labevents": 2,
        "microbiologyevents": 2,
        "transfers": 2,
        "chartevents": 1,
        "inputevents_cv": 1,
        "outputevents": 1,
        "d_items": 0,
        "d_labitems": 0,
        "d_icd_diagnoses": 0,
        "d_icd_procedures": 0
    }

    pos = {}
    layer_x = {}
    for node, layer in layers.items():
        layer_x.setdefault(layer, 0)
        pos[node] = (layer_x[layer], layer)
        layer_x[layer] += 1
    return pos

# =====================
# Draw graph
# =====================
def draw_graph(G, pos, title, filename):
    plt.figure(figsize=(20, 14))
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color="#E3F2FD", edgecolors="#1565C0")
    nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, edge_color="#555", width=1.5)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Edge labels (join keys)
    edge_labels = {(u, v): d["key"] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)

    plt.title(title, fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()
    print(f"✅ Saved {filename}")

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    G = build_schema_graph()

    # Spring layout
    spring_pos = nx.spring_layout(G, seed=42, k=1.2)
    draw_graph(G, spring_pos, "MIMIC-III Schema Graph (Spring Layout)", "schema_graph_spring.png")

    # Layered layout
    layered_pos = layered_layout()
    draw_graph(G, layered_pos, "MIMIC-III Schema Graph (Layered Layout)", "schema_graph_layered.png")

    # Join path demo
    print("\n🔍 Example join paths:")
    print("patients → labevents:", nx.shortest_path(G, "patients", "labevents"))
    print("patients → d_items:", nx.shortest_path(G, "patients", "d_items"))
