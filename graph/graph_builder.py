# graph_builder.py
import networkx as nx
from .tables import tables

def build_schema_graph():
    G = nx.DiGraph()

    for table_name, info in tables.items():
        G.add_node(table_name, **info)
        for foreign_key in info["foreign_keys"]:
            parent = foreign_key["table"]
            relation = {"parent_key": foreign_key["references"], "child_key": foreign_key["column"]}
            if G.has_edge(parent, table_name):
                G[parent][table_name]["relations"].append(relation)
            else:
                G.add_edge(parent, table_name, key=foreign_key["column"],
                           parent_key=foreign_key["references"], relations=[relation])


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
                forward = edge is not None
                if edge is None:
                    edge = graph.get_edge_data(right, left)
                joins.append({"left": left, "right": right, "key": edge["key"],
                              "left_key": edge["parent_key"] if forward else edge["key"],
                              "right_key": edge["key"] if forward else edge["parent_key"]})
            paths.append({"source": source, "target": target, "joins": joins})

    return paths
