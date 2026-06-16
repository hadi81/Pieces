import subprocess
import re
from collections import defaultdict
from itertools import combinations


def run_wpa(wpa_bin, bc_file, output_file):
    cmd = [
        wpa_bin,
        "-ander",
        "-svfg",
        "-dump-mssa",
        "-dump-pag",
        bc_file
    ]

    with open(output_file, "w") as f:
        subprocess.run(cmd, stdout=f, check=False)


def load_ignore_list(ignore_file):

    ignore_set = set()

    try:
        with open(ignore_file) as f:
            for line in f:
                name = line.strip()
                if name and not name.startswith("#"):
                    ignore_set.add(name)
    except FileNotFoundError:
        pass

    return ignore_set


def load_noalias_functions(noalias_file):

    funcs = []

    with open(noalias_file) as f:
        for line in f:
            name = line.strip()

            if name and not name.startswith("#"):
                funcs.append(name)

    return funcs


def parse_mssa(output_file, ignore_funcs):

    func_regions = defaultdict(dict)

    current_func = None

    func_pattern = re.compile(r"=+FUNCTION:\s*(.+?)=+")
    mr_pattern = re.compile(r"MR_(\d+)")
    pts_pattern = re.compile(r"pts\{([^}]*)\}")

    with open(output_file) as f:

        for line in f:

            func_match = func_pattern.search(line)

            if func_match:

                func_name = func_match.group(1).strip()

                if func_name in ignore_funcs:
                    current_func = None
                else:
                    current_func = func_name

                continue

            if current_func is None:
                continue

            mr_match = mr_pattern.search(line)

            if not mr_match:
                continue

            mr = f"MR_{mr_match.group(1)}"

            pts_set = set()

            pts_match = pts_pattern.search(line)

            if pts_match:

                pts_vals = pts_match.group(1).split()

                for p in pts_vals:
                    try:
                        pts_set.add(int(p))
                    except ValueError:
                        pass

            func_regions[current_func][mr] = pts_set

    return func_regions


def build_noalias_alias_map(func_regions, noalias_funcs):

    result = {}
    union_pts = set()

    valid_funcs = [f for f in noalias_funcs if f in func_regions]

    for f1 in valid_funcs:

        per_func = {}

        mr1 = set(func_regions[f1].keys())

        for f2 in valid_funcs:

            if f1 == f2:
                continue

            mr2 = set(func_regions[f2].keys())

            common_mr = mr1.intersection(mr2)

            if not common_mr:
                continue

            pts_shared = set()

            for mr in common_mr:

                pts1 = func_regions[f1].get(mr, set())
                pts2 = func_regions[f2].get(mr, set())

                pts_shared |= pts1.intersection(pts2)

            if pts_shared:

                per_func[f2] = sorted(pts_shared)

                union_pts |= pts_shared

        if per_func:
            result[f1] = per_func

    return result, sorted(union_pts)


def compute_noalias_alias_map(
    wpa_bin,
    bc_file,
    ignore_file,
    noalias_file,
    output_file="mssa_dump"):

    ignore_funcs = load_ignore_list(ignore_file)

    run_wpa(wpa_bin, bc_file, output_file)

    func_regions = parse_mssa(output_file, ignore_funcs)

    noalias_funcs = load_noalias_functions(noalias_file)

    alias_map, union_pts = build_noalias_alias_map(func_regions, noalias_funcs)

    return alias_map, union_pts


import re


def extract_pts_from_mssa_node(node):

    node_id, attrs = node
    label = attrs.get("label", "")

    mssa_types = [
        "ActualINSVFGNode",
        "ActualOUTSVFGNode",
        "FormalINSVFGNode",
        "FormalOUTSVFGNode",
        "IntraMSSAPHISVFGNode"
    ]

    # check if node is MSSA node
    if not any(t in label for t in mssa_types):
        return []

    # extract pts set
    # pts_pattern = re.search(r'pts\{([^}]*)\}', label)
    pts_pattern = re.search(r'pts\\?\{([^}]*)\\?\}', label)

    if not pts_pattern:
        return []

    pts = []

    for p in pts_pattern.group(1).split():
        try:
            pts.append(int(p))
        except ValueError:
            pass

    return pts