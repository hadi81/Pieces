from networkx.drawing.nx_agraph import read_dot
import networkx as nx
import re
import sys

DOT_FILE = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"


# ------------------------------------------------------------
# Extract pts IDs from a node label
# ------------------------------------------------------------
def parse_pts(label):
    """
    Extract pts{...} object IDs from SVFG node label.
    Returns a set of integers.
    """
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
def find_global_node(G, global_name):
    for node, data in G.nodes(data=True):
        label = data.get("label", "")
        if ("AddrVFGNode" in label and
            "GlobalValVar" in label and
            global_name in label):
            return node
    return None


# ------------------------------------------------------------
# Alias-constrained DFS
# ------------------------------------------------------------
def analyze_fpin_alias(G, root, global_pts):
    visited = set()
    stack = [root]

    approachable = []
    not_approachable = []

    while stack:
        node = stack.pop()

        if node in visited:
            continue

        visited.add(node)
        label = G.nodes[node].get("label", "")

        # Check FPIN nodes
        if "FormalINSVFGNode" in label:
            fpin_pts = parse_pts(label)

            if fpin_pts and fpin_pts.intersection(global_pts):
                approachable.append((node, fpin_pts))
            else:
                not_approachable.append((node, fpin_pts))

        # Continue traversal
        for succ in G.successors(node):
            stack.append(succ)

    return approachable, not_approachable


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python alias_fpin_analysis.py <global_variable_name>")
        sys.exit(1)

    global_name = sys.argv[1]

    print("Loading graph...")
    G = read_dot(DOT_FILE)
    print("Loaded.")
    print("Nodes:", len(G.nodes()))
    print("Edges:", len(G.edges()))

    print("\nFinding global node:", global_name)
    root = find_global_node(G, global_name)

    if root is None:
        print("Global node not found.")
        sys.exit(1)

    print("Found global node:", root)

    global_label = G.nodes[root].get("label", "")
    global_pts = parse_pts(global_label)

    print("\nGlobal PTS:", global_pts)

    print("\nRunning alias-constrained DFS...")
    approachable, not_approachable = analyze_fpin_alias(G, root, global_pts)

    print("\n============================")
    print("Approachable FPIN nodes:")
    print("============================")

    for node, pts in approachable:
        print(node, "PTS:", pts)

    print("\n============================")
    print("Not Approachable FPIN nodes:")
    print("============================")

    for node, pts in not_approachable:
        print(node, "PTS:", pts)

    print("\nSummary:")
    print("Approachable FPIN count:", len(approachable))
    print("Not Approachable FPIN count:", len(not_approachable))


if __name__ == "__main__":
    main()
