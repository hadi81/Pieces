import networkx as nx

# Load DOT file
dot_file = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"
G = nx.drawing.nx_pydot.read_dot(dot_file)

# Convert to directed graph (sometimes DOT loads as MultiGraph)
G = nx.DiGraph(G)

def find_node_by_label(keyword):
    for node, data in G.nodes(data=True):
        label = data.get("label", "")
        if keyword in label:
            return node
    return None

# ---- CHANGE THIS depending on what you want ----
root_keyword = "interpreter_temperature_model"
# root_keyword = "@interpreter_second_temperature_model"

root = find_node_by_label(root_keyword)

if root is None:
    print("Root not found.")
    exit()

print(f"Root node: {root}")

# Forward slice (reachable nodes)
reachable = nx.descendants(G, root)
reachable.add(root)

print(f"Total reachable nodes: {len(reachable)}")

# Check which task functions are reachable
input_task = False
second_task = False

for node in reachable:
    label = G.nodes[node].get("label", "")
    if "_Z14TFLM_InputTaskf" in label:
        input_task = True
    if "_Z21TFLM_Second_InputTaskf" in label:
        second_task = True

print("Includes TFLM_InputTask:", input_task)
print("Includes TFLM_Second_InputTask:", second_task)