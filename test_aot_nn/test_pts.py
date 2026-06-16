#!/usr/bin/env python3
"""
SVFG slicing that separates flows of two interpreters in a context-insensitive SVFG.

Key idea:
- Compute object IDs associated with each task (pts{...})
- Remove shared "bridge" object IDs (e.g. 907)
- During BFS:
    * Always traverse "neutral" nodes that have no pts{}
    * Traverse nodes whose pts{} intersects UNIQUE object IDs for that slice
    * Do NOT traverse nodes that have pts{} but no intersection with UNIQUE set
This prevents leakage through shared objects while still allowing traversal through
SVFG structural nodes that carry no pts{} annotations.
"""

import re
from collections import deque
from networkx.drawing.nx_agraph import read_dot

DOT_FILE = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"

TASK_A = "_Z14TFLM_InputTaskf"
TASK_B = "_Z21TFLM_Second_InputTaskf"

ROOT_A_KEY = "@interpreter_temperature_model"
ROOT_B_KEY = "@interpreter_second_temperature_model"

LOG_EVERY = 50000

PTS_RE = re.compile(r"pts\\\{([^}]*)\\\}")

def parse_pts(label):
    pts = set()
    for m in PTS_RE.finditer(label or ""):
        for x in re.findall(r"\d+", m.group(1)):
            pts.add(int(x))
    return pts

def find_node_by_label_substring(G, needle):
    scanned = 0
    for n, data in G.nodes(data=True):
        scanned += 1
        if scanned % LOG_EVERY == 0:
            print(f"[scan] find_node('{needle}') scanned {scanned} nodes...", flush=True)
        if needle in (data.get("label", "") or ""):
            return n
    return None

def extract_task_objects(G, task_mangled):
    objs = set()
    scanned = 0
    hits = 0
    for n, data in G.nodes(data=True):
        scanned += 1
        if scanned % LOG_EVERY == 0:
            print(f"[scan] extract_task_objects({task_mangled}) scanned {scanned}, hits={hits}...", flush=True)
        label = data.get("label", "") or ""
        if task_mangled in label:
            hits += 1
            objs |= parse_pts(label)
    print(f"[info] extract_task_objects({task_mangled}) hits={hits}", flush=True)
    return objs

def object_partitioned_bfs(G, root, unique_objs):
    """
    BFS that:
      - Always expands neutral nodes (no pts{})
      - Expands nodes whose pts intersects unique_objs
      - Stops at nodes that have pts but do not intersect unique_objs
    """
    visited = set()
    q = deque([root])

    expanded = 0
    while q:
        u = q.popleft()
        if u in visited:
            continue
        visited.add(u)

        label = G.nodes[u].get("label", "") or ""
        pts_u = parse_pts(label)

        # If node has pts but isn't in our unique object region, do not expand it.
        if pts_u and not (pts_u & unique_objs):
            continue

        for v in G.successors(u):
            if v not in visited:
                q.append(v)

        expanded += 1
        if expanded % LOG_EVERY == 0:
            print(f"[bfs] expanded {expanded} nodes from root={root}", flush=True)

    return visited

def slice_contains(G, slice_nodes, keyword):
    for n in slice_nodes:
        if keyword in (G.nodes[n].get("label", "") or ""):
            return True
    return False

def main():
    print("Loading graph...", flush=True)
    G = read_dot(DOT_FILE)
    print("Loaded.", flush=True)
    print("Nodes:", len(G.nodes()), flush=True)
    print("Edges:", len(G.edges()), flush=True)
    print()

    print("Extracting pts-object IDs for tasks...", flush=True)
    objsA = extract_task_objects(G, TASK_A)
    objsB = extract_task_objects(G, TASK_B)

    shared = objsA & objsB
    uniqueA = objsA - objsB
    uniqueB = objsB - objsA

    print("\nObjects associated with TFLM_InputTask:", objsA, flush=True)
    print("Objects associated with TFLM_Second_InputTask:", objsB, flush=True)
    print("\nUnique objects for A:", uniqueA, flush=True)
    print("Unique objects for B:", uniqueB, flush=True)
    print("Shared objects (bridges):", shared, flush=True)
    print()

    print("Finding interpreter roots...", flush=True)
    rootA = find_node_by_label_substring(G, ROOT_A_KEY)
    rootB = find_node_by_label_substring(G, ROOT_B_KEY)
    print("RootA:", rootA, flush=True)
    print("RootB:", rootB, flush=True)
    print()

    if rootA is None or rootB is None:
        raise SystemExit("ERROR: Could not find one or both interpreter roots.")

    print("Computing object-partitioned slices...", flush=True)
    sliceA = object_partitioned_bfs(G, rootA, uniqueA)
    sliceB = object_partitioned_bfs(G, rootB, uniqueB)

    print("SliceA size:", len(sliceA), flush=True)
    print("SliceB size:", len(sliceB), flush=True)
    print()

    print("==== RESULTS ====", flush=True)
    print("SliceA -> InputTask:        ", slice_contains(G, sliceA, TASK_A), flush=True)
    print("SliceA -> SecondInputTask:  ", slice_contains(G, sliceA, TASK_B), flush=True)
    print()
    print("SliceB -> InputTask:        ", slice_contains(G, sliceB, TASK_A), flush=True)
    print("SliceB -> SecondInputTask:  ", slice_contains(G, sliceB, TASK_B), flush=True)
    print()
    print("Shared bridge objects count:", len(shared), flush=True)

if __name__ == "__main__":
    main()