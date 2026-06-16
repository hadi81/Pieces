import networkx as nx
from networkx.drawing.nx_agraph import read_dot, write_dot


def find_global_node(G, variable_name):
    """
    Locate the node representing a given global variable.
    """
    for node, data in G.nodes(data=True):

        label = data.get("label", "")

        if (
            "GlobalValVar" in label
            and variable_name in label
        ):
            return node

    return None


def dump_descendant_subgraph(dot_file, variable_name, out_file):

    print("Loading graph...")
    G = read_dot(dot_file)

    print("Searching variable...")
    start_node = find_global_node(G, variable_name)

    if start_node is None:
        print("Variable not found.")
        return

    print("Start node:", start_node)

    # get all descendants
    descendants = nx.descendants(G, start_node)

    nodes = set(descendants)
    nodes.add(start_node)

    subgraph = G.subgraph(nodes).copy()

    print("Nodes in subgraph:", len(subgraph.nodes()))
    print("Edges in subgraph:", len(subgraph.edges()))

    print("Writing graph...")
    write_dot(subgraph, out_file)

    print("Done.")


if __name__ == "__main__":

    # dump_descendant_subgraph(
    #     "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot",
    #     "interpreter_temperature_model",
    #     "interpreter_temperature_model_subgraph.dot"
    # )

    dump_descendant_subgraph(
        "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot",
        "g_temperature_int8_model_data",
        "g_temperature_int8_model_data_subgraph.dot"
    )

    dump_descendant_subgraph(
        "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot",
        "temperature_model_tensor_arena",
        "temperature_model_tensor_arena_subgraph.dot"
    )
