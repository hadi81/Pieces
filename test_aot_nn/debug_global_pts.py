from networkx.drawing.nx_agraph import read_dot
import re
import sys

DOT_FILE = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"


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


def find_global_node(G, global_name):
    for node, data in G.nodes(data=True):
        label = data.get("label", "")
        if ("AddrVFGNode" in label and
            "GlobalValVar" in label and
            global_name in label):
            return node
    return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_global_pts.py <global_variable_name>")
        sys.exit(1)

    global_name = sys.argv[1]

    print("Loading graph...")
    G = read_dot(DOT_FILE)
    print("Loaded.")

    root = find_global_node(G, global_name)

    if root is None:
        print("Global node not found.")
        return

    print("\nRoot node ID:", root)
    label = G.nodes[root].get("label", "")

    print("\nFull label:\n")
    print(label)

    pts = parse_pts(label)

    print("\nParsed PTS set:", pts)
    print("PTS size:", len(pts))


if __name__ == "__main__":
    main()
