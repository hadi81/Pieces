from networkx.drawing.nx_agraph import read_dot
import networkx as nx
import re
import sys

DOT_FILE = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"


# ------------------------------------------------------------
# Extract pts IDs
# ------------------------------------------------------------
def parse_pts(label):
    pts = set()
    match = re.search(r'pts\{([^}]*)\}', label)
    if not match:
        return pts

    contents = match.group(1).strip()
    if not contents:
        return pts

    for token in contents.split():
        try:
            pts.add(int(token))
        except ValueError:
            continue

    return pts


# ------------------------------------------------------------
# Find global AddrVFGNode
# ------------------------------------------------------------
def find_global_addr_node(G, global_name):
    for node, data in G.nodes(data=True):
        label = data.get("label", "")
        if ("AddrVFGNode" in label and
            "GlobalValVar" in label and
            global_name in label):
            return node
    return None


# ------------------------------------------------------------
# Find first reachable node with non-empty pts
# ------------------------------------------------------------
def find_first_pts_node(G, root):
    visited = set()
    stack = [root]

    while stack:
        node = stack.pop()

        if node in visited:
            continue
        visited.add(node)

        label = G.nodes[node].get("label", "")
        pts = parse_pts(label)

        if pts:
            return node, pts

        for succ in G.successors(node):
            stack.append(succ)

    return None, set()


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_real_root.py <global_variable_name>")
        sys.exit(1)

    global_name = sys.argv[1]

    print("Loading graph...")
    G = read_dot(DOT_FILE)
    print("Loaded.")
    print("Nodes:", len(G.nodes()))
    print("Edges:", len(G.edges()))

    print("\nFinding AddrVFGNode for:", global_name)
    addr_node = find_global_addr_node(G, global_name)

    if addr_node is None:
        print("Global AddrVFGNode not found.")
        sys.exit(1)

    print("\nAddrVFGNode:", addr_node)
    print("Label:\n", G.nodes[addr_node].get("label", ""))

    print("\nSearching for first reachable node with pts...")

    pts_node, pts_set = find_first_pts_node(G, addr_node)

    if pts_node is None:
        print("No reachable node with non-empty pts found.")
        sys.exit(0)

    print("\n========== REAL OBJECT ROOT ==========")
    print("Node:", pts_node)
    print("PTS:", pts_set)
    print("Label:\n", G.nodes[pts_node].get("label", ""))
    print("=======================================")


if __name__ == "__main__":
    main()
