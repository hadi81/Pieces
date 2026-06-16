import networkx as nx
# from networkx.drawing.nx_pydot import read_dot
# from networkx.drawing.nx_pydot import write_dot
from networkx.drawing.nx_agraph import write_dot
from networkx.drawing.nx_agraph import read_dot
import pydot
from datetime import datetime
from IPython import embed

import re
import sys
import os
import tempfile

import subprocess
from utils.mssa_helper import compute_noalias_alias_map, extract_pts_from_mssa_node

WPA_BIN = "/home/hzm5471/repos/SVF/Debug-build/wpa/../bin/wpa"
BC_FILE = "/home/hzm5471/repos/TensorFlow-with-Stm32f769-Clang/Prj3/Clang/build/stm32AiApp.elf.bc"

IGNORE_FILE = "/home/hzm5471/repos/new_pieces/Pieces/my_custom_driver_files/rtmk.ignore"
NOALIAS_FILE = "/home/hzm5471/repos/new_pieces/Pieces/my_custom_driver_files/rtmk.noalias"


def dump_subgraph(new_ddg, node_name, suffix):
    
    cnt = 1
    for var in new_ddg.nodes(data=True):
        if node_name in var[0]:
            reachable = nx.descendants(new_ddg, var[0])
            reachable.add(var[0])
            sub = new_ddg.subgraph(reachable).copy()
            name = str(cnt) + node_name + suffix + ".dot"
            cnt = cnt + 1
            from networkx.drawing.nx_agraph import write_dot
            write_dot(sub, name)

def print_all_nodes(new_ddg, node_name):    

    for var in new_ddg.nodes(data=True):
        if node_name in var[0]:
            print(var)

def print_all_nodes_a1(new_ddg, node_name):    
    count = 0
    glob_count = 0
    for var in new_ddg.nodes(data=True):
        if node_name in var[1]["label"]:
            count = count + 1
            if "AddrVFGNode" in var[1]["label"] and 'GlobalValVar' in var[1]["label"]:
                glob_count = glob_count + 1
            print(var)
            print("\n")
    print("count: " + str(count))
    print("glob_count: " + str(glob_count))

def print_all_nodes_keys_a1(new_ddg, node_name):    
    count = 0
    glob_count = 0
    for var in new_ddg.nodes(data=True):
        if node_name in var[1]["label"]:
            count = count + 1
            if "AddrVFGNode" in var[1]["label"] and 'GlobalValVar' in var[1]["label"]:
                glob_count = glob_count + 1
            print(var[0])
            print("\n")
    print("count: " + str(count))
    print("glob_count: " + str(glob_count))

def dump_subgraph_a1(new_ddg, node_name, suffix):
    
    cnt = 1
    for var in new_ddg.nodes(data=True):
        if node_name in var[1]["label"]:
            reachable = nx.descendants(new_ddg, var[0])
            reachable.add(var[0])
            sub = new_ddg.subgraph(reachable).copy()
            name = str(cnt) + node_name + suffix + ".dot"
            cnt = cnt + 1
            from networkx.drawing.nx_agraph import write_dot
            write_dot(sub, name)

def dump_subgraph_a1_global(new_ddg, node_name, suffix):
    
    cnt = 1
    for var in new_ddg.nodes(data=True):
        if node_name in var[1]["label"] and "AddrVFGNode" in var[1]["label"] and 'GlobalValVar' in var[1]["label"]:
            reachable = nx.descendants(new_ddg, var[0])
            reachable.add(var[0])
            sub = new_ddg.subgraph(reachable).copy()
            name = str(cnt) + node_name + suffix + ".dot"
            cnt = cnt + 1
            from networkx.drawing.nx_agraph import write_dot
            write_dot(sub, name)

def dump_subgraph_a2(new_ddg, node_name, suffix):
    
    cnt = 1
    for var in new_ddg.nodes(data=True):
        if node_name in var[0]:
            reachable = nx.descendants(new_ddg, var[0])
            reachable.add(var[0])
            sub = new_ddg.subgraph(reachable).copy()
            name = str(cnt) + node_name + suffix + ".dot"
            cnt = cnt + 1
            from networkx.drawing.nx_agraph import write_dot
            write_dot(sub, name)

class Analysis:
    def __init__(self):
        self.cfg = None
        self.pddg = None
        self.pdg = None

analysis = Analysis()

def quote_if_needed(s):
    """Quote strings that contain special DOT characters."""
    if isinstance(s, str) and (':' in s or ' ' in s or '-' in s):
        return f'"{s}"'
    return s

def convert_to_pydot_safe(graph):
    pdot = pydot.Dot(graph_type='digraph')

    for n, attrs in graph.nodes(data=True):
        n_quoted = quote_if_needed(n)
        clean_attrs = {k: quote_if_needed(v) for k, v in attrs.items()}
        pdot.add_node(pydot.Node(n_quoted, **clean_attrs))

    for u, v, attrs in graph.edges(data=True):
        u_quoted = quote_if_needed(u)
        v_quoted = quote_if_needed(v)
        clean_attrs = {k: quote_if_needed(v) for k, v in attrs.items()}
        pdot.add_edge(pydot.Edge(u_quoted, v_quoted, **clean_attrs))

    return pdot

def merge_graphs(dg, cg):
    pdg = nx.DiGraph()
    pdg.add_nodes_from(dg.nodes(data=True))
    pdg.add_nodes_from(cg.nodes(data=True))

    for u, v, data in dg.edges(data=True):
        if 'type' in dg.nodes[u] and dg.nodes[u]['type'] == 'function':
            # from IPython import embed; embed()
            pdg.add_edge(u, v, dep="control", **data)
        else:
            pdg.add_edge(u, v, dep="data", **data)

    for u, v, data in cg.edges(data=True):
        if 'type' in cg.nodes[u] and cg.nodes[u]['type'] == 'function':
            pdg.add_edge(u, v, dep="control", **data)
        else:
            pdg.add_edge(u, v, dep="data", **data)

    # from IPython import embed
    # embed()
    # nx.readwrite.gpickle.write_gpickle(pdg, "gen_pdg.gpickle")
    # write_dot(pdg, "gen_pdg.dot")
    return pdg

def replace_node(G, old_node, new_node):

    # from IPython import embed; embed()
    # nx.relabel_nodes(G, {old_node: new_node}, copy=False)
    G.add_node(new_node, **G.nodes[old_node])

    if (isinstance(G, nx.MultiDiGraph)):
        for pred in G.predecessors(old_node):
            if not pred == new_node:
                for key, attr in G[pred][old_node].items():
                    G.add_edge(pred, new_node, key=key, **attr)
        for succ in G.successors(old_node):
            if not succ == new_node:
                for key, attr in G[old_node][succ].items():
                    G.add_edge(new_node, succ, key=key, **attr)

    elif (isinstance(G, nx.DiGraph)):
        for pred in list(G.predecessors(old_node)):
            if not pred == new_node:
                attr = G.get_edge_data(pred, old_node)
                G.add_edge(pred, new_node, **attr)
        for succ in list(G.successors(old_node)):
            if not succ == new_node:
                attr = G.get_edge_data(old_node, succ)
                G.add_edge(new_node, succ, **attr)

    G.remove_node(old_node)

def replace_node_old(G, old_node, new_node):

    # if new_node == "AHBPrescTable":
    #     from IPython import embed; embed()

    G.add_node(new_node, **G.nodes[old_node])

    if (isinstance(G, nx.MultiDiGraph)):

    #     if old_node == "AHBPrescTable":
    #         print(old_node)
    #         print(new_node)
    #         from IPython import embed; embed()
        
    #     if new_node == "AHBPrescTable":
    #         print(old_node)
    #         print(new_node)
    #         from IPython import embed; embed()

        for pred in G.predecessors(old_node):
            if not pred == new_node:
                for key, attr in G[pred][old_node].items():
                    G.add_edge(pred, new_node, key=key, **attr)
        for succ in G.successors(old_node):
            if not succ == new_node:
                for key, attr in G[old_node][succ].items():
                    G.add_edge(new_node, succ, key=key, **attr)

        # if old_node == "AHBPrescTable":
        #     print(old_node)
        #     print(new_node)
        #     from IPython import embed; embed()
        
        # if new_node == "AHBPrescTable":
        #     print(old_node)
        #     print(new_node)
        #     from IPython import embed; embed()

    elif (isinstance(G, nx.DiGraph)):
        # from IPython import embed; embed()
        for pred in list(G.predecessors(old_node)):
            if not pred == new_node:
                attr = G.get_edge_data(pred, old_node)
                G.add_edge(pred, new_node, **attr)
        for succ in list(G.successors(old_node)):
            if not succ == new_node:
                attr = G.get_edge_data(old_node, succ)
                G.add_edge(new_node, succ, **attr)
    # if old_node == "AHBPrescTable":
    #     print(old_node)
    #     print(new_node)
    #     from IPython import embed; embed()
    
    # if new_node == "AHBPrescTable":
    #     print(old_node)
    #     print(new_node)
    #     from IPython import embed; embed()

    G.remove_node(old_node)

def load_cfg_light(bc):
    path = "/home/hzm5471/repos/SVF/pieces/cfg_graph_for_pieces.dot"
    # cmd = ["opt", "-enable-new-pm=0", "-dot-callgraph", "-disable-output", bc]
    # subprocess.run(cmd)
    # cmd = ["cp", bc + ".callgraph.dot", path]
    # subprocess.run(cmd)

    cfg = read_dot(path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)

    for n in list(cfg.nodes(data=True)):
        # fun = '"{function_name}"'
        if ("label" in n[1]):
            label = n[1]["label"]
            match = re.search(r'fun:\s*([^\\}]+)', label)
            fun = match.group(1).strip()
            # fun = n[1]["label"][2:-2]
            # from IPython import embed; embed()
            replace_node(cfg, n[0], fun)
            cfg.nodes[fun]['type'] = 'function'
    # from IPython import embed; embed()
    return cfg

def load_cfg_svf(bc):
    path = "/home/hzm5471/repos/SVF/pieces/icfg_graph_for_pieces.dot"
    # cmd = [os.environ["SVF"], bc, "-dump-icfg"]
    # subprocess.run(cmd, stdout=subprocess.DEVNULL)

    # cmd = ["cp", "./icfg_initial_dot", path]
    # subprocess.run(cmd)

    # cmd = ["rm", "./icfg_initial_dot"]
    # subprocess.run(cmd)

    cfg = read_dot(path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)

    # print("Load ICFG embed")
    # from IPython import embed; embed()

    for n in list(cfg.nodes(data=True)):
        name = n[0]
        if ':' in name:
            name = name.split(':')[0]
            replace_node(cfg, n[0], name)
    for n in list(cfg.nodes(data=True)):
        if ("label" in n[1]):
            if "GlobalICFGNode" in n[1]["label"]:
                continue
            elif any(sub in n[1]["label"] for sub in ["CallICFGNode", "RetICFGNode"]):
                caller = n[1]["label"].split("{fun: ")[1].split('\\')[0]
                replace_node(cfg, n[0], caller)
                cfg.nodes[caller]['type'] = 'function'

                # callee = n[1]["label"].split("call")[1]
                label = n[1].get("label", "")

                if "call" in label:
                    parts = label.split("call", 1)
                    if len(parts) > 1:
                        callee = parts[1]
                    else:
                        continue
                else:
                    continue

                if '@' in callee and '(' in callee:
                    callee = callee.split('@')[1].split('(')[0]
                else:
                    continue
                cfg.add_edge(caller, callee)
                cfg.nodes[callee]['type'] = 'function'
            elif "{fun: " in n[1]["label"]:
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]
                replace_node(cfg, n[0], fun)
                cfg.nodes[fun]['type'] = 'function'
    
    new_cfg = nx.DiGraph()
    functions = [(n, d) for n, d in cfg.nodes(data=True) if d.get("type") == 'function']

    new_cfg.add_nodes_from(functions)

    for f1 in functions:
        # if "__cxx_global_var" in f1[0]:
        #     print("Ignorng auto generated global variable in CFG: " + f1[0])
        reachable = nx.descendants(cfg, f1[0])
        for f2 in functions:
            # from IPython import embed; embed()
            if f2[0] in reachable:
                new_cfg.add_edge(f1[0], f2[0])

    for node in list(new_cfg.nodes(data=True)):
        # from IPython import embed; embed()
        if ("label" in node[1]):
            if any(sub in node[1]["label"] for sub in ["CallICFGNode", "RetICFGNode"]):
                data = node[1]["label"].split("{fun: ")[1].split('\\')[0]
                node[1]["name"] = data
            elif "{fun: " in n[1]["label"]:
                fun = node[1]["label"].split('{fun: ')[1].split('\\')[0]
                node[1]["name"] = fun
            else:
                print("Invalid node")
                print(node[1]["label"])
                print("\n")
        elif ("type" in node[1]):
            # from IPython import embed; embed()
            node[1]["name"] = node[0]
            # from IPython import embed; embed()
        else:
            pass  # print("Invalid label node")
            # print(node[1])
            # print(node)
            print("\n")
        # from IPython import embed; embed()
    # from IPython import embed; embed()
    
    print("new_cfg embed")
    from IPython import embed; embed()

    return new_cfg

def load_cfg_svf_new(bc):
    path = "/home/hzm5471/repos/SVF/pieces/icfg_graph_for_pieces.dot"
    # cmd = [os.environ["SVF"], bc, "-dump-icfg"]
    # subprocess.run(cmd, stdout=subprocess.DEVNULL)

    # cmd = ["cp", "./icfg_initial_dot", path]
    # subprocess.run(cmd)

    # cmd = ["rm", "./icfg_initial_dot"]
    # subprocess.run(cmd)
    
    cfg = read_dot(path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)

    # print("Load ICFG embed")
    # from IPython import embed; embed()

    for n in list(cfg.nodes(data=True)):
        name = n[0]
        if ':' in name:
            name = name.split(':')[0]
            replace_node(cfg, n[0], name)
    for n in list(cfg.nodes(data=True)):
        if ("label" in n[1]):
            if "GlobalICFGNode" in n[1]["label"]:
                continue
            elif any(sub in n[1]["label"] for sub in ["CallICFGNode", "RetICFGNode"]):
                caller = n[1]["label"].split("{fun: ")[1].split('\\')[0]
                # from IPython import embed; embed()
                # replace_node(cfg, n[0], caller)
                cfg.nodes[n[0]]['name'] = caller
                # cfg.nodes[caller]['type'] = 'function'
                cfg.nodes[n[0]]['type'] = 'function'

                # callee = n[1]["label"].split("call")[1]
                # label = n[1].get("label", "")

                # if "call" in label:
                #     parts = label.split("call", 1)
                #     if len(parts) > 1:
                #         callee = parts[1]
                #     else:
                #         continue
                # else:
                #     continue

                # if '@' in callee and '(' in callee:
                #     callee = callee.split('@')[1].split('(')[0]
                # else:
                #     continue
                # cfg.add_edge(caller, callee)
                # cfg.nodes[callee]['type'] = 'function'
                # from IPython import embed; embed()
            elif "{fun: " in n[1]["label"]:
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]
                # replace_node(cfg, n[0], fun)
                cfg.nodes[n[0]]['name'] = fun
                # cfg.nodes[fun]['type'] = 'function'
                cfg.nodes[n[0]]['type'] = 'function'
    
    new_cfg = nx.DiGraph()
    functions = [(n, d) for n, d in cfg.nodes(data=True) if d.get("type") == 'function']

    # from IPython import embed; embed()

    new_cfg.add_nodes_from(functions)

    for f1 in functions:
        reachable = nx.descendants(cfg, f1[0])
        # from IPython import embed; embed()
        for f2 in functions:
            if f2[0] in reachable:
                # from IPython import embed; embed()
                new_cfg.add_edge(f1[0], f2[0])

    return new_cfg

def load_ddg_light(bc):
    path = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"
    # path = "/home/hzm5471/repos/SVF/Debug-build/pieces_test/bak/light-ddg_dot"
    # cmd = [os.environ["SVF_BIN"] + "/svf-pieces", f'bc={bc}', f'ddg={path}', '-use-def', '-ffmap', '-get-threads']
    # subprocess.run(cmd)
    
    ddg = read_dot(path)
    cmd = ["rm", path]
    subprocess.run(cmd)

    for n in list(ddg.nodes(data=True)):
        if ("label" in n[1]):
            data = n[1]["label"]
            replace_node(ddg, n[0], data)

    return ddg

def load_ddg_svf(bc):
    # first, generate the different maps
    cmd = [os.environ["SVF_BIN"] + "/svf-pieces", f'bc={bc}', '-ffmap', '-use-def', "-get-threads"]
    subprocess.run(cmd)

    # embed()
    path = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"
    # path = "/home/hzm5471/repos/SVF/Debug-build/pieces_test/bak/svfg_final_dot"
    # cmd = [os.environ["SVF"], bc, "-dump-vfg", "-get-threads"]
    # subprocess.run(cmd, stdout=subprocess.DEVNULL)

    # cmd = ["cp", "./svfg_final_dot", path]
    # subprocess.run(cmd)

    # cmd = ["rm", "./svfg_final_dot"]
    # subprocess.run(cmd)
    
    ddg = read_dot(path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)

    potential_links = []

    control_var1 = True
    num=1
    for n in list(ddg.nodes(data=True)):
        if "AHBPrescTable" in n[1]["label"]:
            if control_var1:
                reachable = nx.descendants(ddg, n[0])
                reachable.add(n[0])
                sub = ddg.subgraph(reachable).copy()
                from networkx.drawing.nx_agraph import write_dot
                name = str(num) + "AHBPrescTable.dot"
                # from IPython import embed; embed()
                write_dot(sub, name)
                num=num+1
                print("found the variable AHBPrescTable in n")
                # from IPython import embed; embed()

        name = n[0]
        if ':' in name:
            name = name.split(':')[0]
            replace_node(ddg, n[0], name)
    for n in list(ddg.nodes(data=True)):
        if ("label" in n[1]):
            if "AddrVFGNode" in n[1]["label"] and 'GlobalValVar' in n[1]["label"]:
                # from IPython import embed; embed()
                # for func in ddg.successors(n[0]):
                    # d1 = func[1]["label"].split('@')[1].split(' ')[0]
                    # d2 = n[1]["label"].split('@')[1].split(' ')[0]
                    # print(d1 + " affects " + d2)
                    # print(
                    # ddg.nodes[func]["label"].split('@')[1].split(' ')[0]
                    # + " affects " +
                    # ddg.nodes[n[0]]["label"].split('@')[1].split(' ')[0]
                    # )
                    # from IPython import embed; embed()

                # from IPython import embed; embed()
                data = n[1]["label"].split('@')[1].split(' ')[0]
                # replace_node(ddg, n[0], data)
                ddg.nodes[n[0]]["type"] = 'global'
                # ddg.nodes[data]["type"] = 'global'
                # from IPython import embed; embed()
            elif "AddrVFGNode" in n[1]["label"] and 'FunValVar' in n[1]["label"]:
                data = n[1]["label"].split("\\n")[-1].rstrip("}")
                ddg.nodes[n[0]]["type"] = 'function'

            elif "IntraPHIVFGNode" in n[1]["label"]:
                spos = n[1]["label"].find("@")
                lpos = n[1]["label"].find("%")
                if (not spos == -1) and (spos < lpos or lpos == -1):
                    symbols = n[1]["label"].split("@")
                    try:
                        fun = symbols[1].split('(')[0]
                    except:
                        print(n[1]["label"])
                        exit()
                    for i in range(2, len(symbols)):
                        ref = symbols[i].split(',')[0]
                        if '(' in ref:
                            ref = ref.split('(')[0]
                        potential_links += [(ref, fun)]
            elif "ActualRetVFGNode" in n[1]["label"]:
                continue
                if not "@" in n[1]["label"]:
                    continue
                fun = n[1]["label"].split("@")[1].split("(")[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
            elif any(sub in n[1]["label"] for sub in ["FormalParmVFGNode", "FormalRetVFGNode"]) and "Fun[" in n[1]["label"]:
                fun = n[1]["label"].split("Fun[")[1].split("]")[0]
                # replace_node(ddg, n[0], fun)
                # ddg.nodes[fun]["type"] = 'function'
                ddg.nodes[n[0]]["type"] = 'function'
            elif "{fun: " in n[1]["label"]:
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]
                # replace_node(ddg, n[0], fun)
                # ddg.nodes[fun]["type"] = 'function'
                ddg.nodes[n[0]]["type"] = 'function'

    # for n in list(ddg.nodes(data=True)):
    #      if ("label" in n[1]):
    #          if "AddrVFGNode" in n[1]["label"] and 'GlobalValVar' in n[1]["label"]:
    #             # from IPython import embed; embed()
    #             for func in ddg.successors(n[0]):
    #                 print(ddg.nodes[func]["label"] + " affects " + n[0])

    # dump_subgraph(ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_old_ddg")

    new_ddg = nx.DiGraph()
    globals = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'global']
    functions = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'function']

    new_ddg.add_nodes_from(globals)
    new_ddg.add_nodes_from(functions)

    # from IPython import embed; embed()
    control_var2 = True
    m=1
    for g in globals:
        if "AHBPrescTable" in g[1]["label"]:
            if control_var2:
                # from IPython import embed; embed()
                reachable = nx.descendants(ddg, g[0])
                reachable.add(g[0])
                sub = ddg.subgraph(reachable).copy()
                from networkx.drawing.nx_agraph import write_dot
                name = str(m) + "gAHBPrescTable.dot" 
                write_dot(sub, name)
                m=m+1
                print("found the variable AHBPrescTable in g")
        reachable = nx.descendants(ddg, g[0])
        # from IPython import embed; embed()
        for f in functions:
            if f[0] in reachable:
                # from IPython import embed; embed()
                new_ddg.add_edge(g[0], f[0])
    #for f1 in functions: // this isn't really the job of the ddg
    #    reachable = nx.descendants(ddg, f1[0])
    #    for f2 in functions:
    #        if f2[0] in reachable:
    #            new_ddg.add_edge(f1[0], f2[0])

    # dump_subgraph(new_ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_new_ddg")

    for link in potential_links:
        if link[0] in new_ddg.nodes:# and new_ddg.nodes[link[0]]['type'] == 'global':
            new_ddg.add_edge(link[0], link[1])
    
    for node in list(new_ddg.nodes(data=True)):
        if ("label" in node[1]):
            if "AddrVFGNode" in node[1]["label"] and 'GlobalValVar' in node[1]["label"]:
                data = node[1]["label"].split('@')[1].split(' ')[0]
                node[1]["name"] = data
            elif any(sub in node[1]["label"] for sub in ["FormalParmVFGNode", "FormalRetVFGNode"]) and "Fun[" in node[1]["label"]:
                fun = node[1]["label"].split("Fun[")[1].split("]")[0]
                node[1]["name"] = fun
            elif "{fun: " in node[1]["label"]:
                fun = node[1]["label"].split('{fun: ')[1].split('\\')[0]
                node[1]["name"] = fun
            else:
                print("Invalid node")
                print(node[1]["label"])
                print("\n")
        else:
            pass  # print("Invalid label node")
            # print(node[1])
            # print("\n")


    # dump_subgraph(new_ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_pot_ddg")
    # for node in list(new_ddg.nodes(data=True)):
    #     node_type =  ddg.nodes[n[0]]["type"]
    #     node_name = node[1]["name"]
    #     print(node_type)
    #     print(node_name)


    return new_ddg

def region_matches(pts, noalias_map, func):

    if func not in noalias_map:
        return False

    pts_set = set(pts)

    for region in noalias_map[func].values():
        if pts_set == set(region):
            return True

    return False


def sanitize_dot_labels(path, max_len=8000):
    """Truncate labels longer than max_len chars so pygraphviz can parse them.
    Truncation point is placed after the @varname so name extraction still works.
    Returns path to a sanitized temp file."""
    sanitized = []
    with open(path, 'r', errors='replace') as f:
        for line in f:
            if len(line) > max_len and 'label=' in line:
                # find the @ symbol (variable name start) and keep enough after it
                at_pos = line.find('@')
                if at_pos != -1:
                    # find end of variable name (space, comma, newline, backslash)
                    end_pos = at_pos + 1
                    while end_pos < len(line) and line[end_pos] not in (' ', ',', '\n', '\\', '"', '='):
                        end_pos += 1
                    keep = line[:end_pos]
                else:
                    keep = line[:max_len]
                # close the label with valid dot syntax
                line = keep + ' ...(truncated)}"];\n'
            sanitized.append(line)
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False)
    tmp.writelines(sanitized)
    tmp.close()
    return tmp.name


def load_ddg_svf_algo1(bc):
    # first, generate the different maps
    cmd = [os.environ["SVF_BIN"] + "/svf-pieces", f'bc={bc}', '-ffmap', '-use-def', "-get-threads", "-get-nn-info",
           "middleware-inc=/home/hzm5471/repos/stm32cubeai/prj1/Middlewares/ST/AI/Inc"]
    subprocess.run(cmd)

    # embed()
    path = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"
    # path = "/home/hzm5471/repos/SVF/Debug-build/pieces_test/bak/svfg_final_dot"
    # cmd = [os.environ["SVF"], bc, "-dump-vfg", "-get-threads"]
    # subprocess.run(cmd, stdout=subprocess.DEVNULL)

    # cmd = ["cp", "./svfg_final_dot", path]
    # subprocess.run(cmd)

    # cmd = ["rm", "./svfg_final_dot"]
    # subprocess.run(cmd)

    sanitized_path = sanitize_dot_labels(path)
    ddg = read_dot(sanitized_path)
    os.unlink(sanitized_path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)
    # dump_subgraph_a1(ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_orig_ddg")

    # dump_subgraph_a1(ddg, "g_untrusted_in", "_orig_ddg")
    # dump_subgraph_a1(ddg, "g_untrusted_in", "_orig_ddg")

    # print("Load SVFG embed")
    # from IPython import embed; embed()
    skip_nodes = (
    "ActualINSVFGNode",
    "ActualOUTSVFGNode",
    "FormalINSVFGNode",
    "FormalOUTSVFGNode",
    "RETMU",
    "IntraMSSAPHISVFGNode",
    "ENCHI"
    )

    potential_links = []

    control_var1 = True
    num=1
    for n in list(ddg.nodes(data=True)):
        # if "AHBPrescTable" in n[1]["label"]:
        #     if control_var1:
        #         reachable = nx.descendants(ddg, n[0])
        #         reachable.add(n[0])
        #         sub = ddg.subgraph(reachable).copy()
        #         from networkx.drawing.nx_agraph import write_dot
        #         name = str(num) + "AHBPrescTable.dot"
        #         # from IPython import embed; embed()
        #         write_dot(sub, name)
        #         num=num+1
        #         print("found the variable AHBPrescTable in n")
                # from IPython import embed; embed()

        name = n[0]
        if ':' in name:
            name = name.split(':')[0]
            replace_node(ddg, n[0], name)
    
    glob_lib_functions = []
    for n in list(ddg.nodes(data=True)):
        if ("label" in n[1]):
            if "AddrVFGNode" in n[1]["label"] and 'GlobalValVar' in n[1]["label"]:
                # from IPython import embed; embed()
                # for func in ddg.successors(n[0]):
                    # d1 = func[1]["label"].split('@')[1].split(' ')[0]
                    # d2 = n[1]["label"].split('@')[1].split(' ')[0]
                    # print(d1 + " affects " + d2)
                    # print(
                    # ddg.nodes[func]["label"].split('@')[1].split(' ')[0]
                    # + " affects " +
                    # ddg.nodes[n[0]]["label"].split('@')[1].split(' ')[0]
                    # )
                    # from IPython import embed; embed()

                # from IPython import embed; embed()
                data = n[1]["label"].split('@')[1].split(' ')[0]
                # print(data)
                # replace_node(ddg, n[0], data)
                ddg.nodes[n[0]]["type"] = 'global'
                # ddg.nodes[data]["type"] = 'global'
                # from IPython import embed; embed()

            elif "AddrVFGNode" in n[1]["label"] and 'FunValVar' in n[1]["label"]:
                data = n[1]["label"].split("\\n")[-1].rstrip("}")
                ddg.nodes[n[0]]["type"] = 'function'
                glob_lib_functions.append(data)

            elif "IntraPHIVFGNode" in n[1]["label"]:
                label = n[1]["label"]
                # truncate at the embedded function body — only parse the PHI header
                cutoff = label.find("; Function Attrs")
                if cutoff == -1:
                    cutoff = label.find("\\ndefine")
                phi_part = label[:cutoff] if cutoff != -1 else label
                spos = phi_part.find("@")
                lpos = phi_part.find("%")
                if (not spos == -1) and (spos < lpos or lpos == -1):
                    symbols = phi_part.split("@")
                    try:
                        fun = symbols[1].split('(')[0]
                    except:
                        print(phi_part)
                        exit()
                    for i in range(2, len(symbols)):
                        ref = symbols[i].split(',')[0]
                        if '(' in ref:
                            ref = ref.split('(')[0]
                        potential_links += [(fun, ref)]
                    # if "= call " in n[1]["label"]:
                    #     ddg.nodes[n[0]]["type"] = 'function'
            elif "ActualRetVFGNode" in n[1]["label"]:
                # ddg.nodes[n[0]]["type"] = 'function'
                continue
                if not "@" in n[1]["label"]:
                    continue
                fun = n[1]["label"].split("@")[1].split("(")[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
            elif any(sub in n[1]["label"] for sub in ["FormalParmVFGNode", "FormalRetVFGNode"]) and "Fun[" in n[1]["label"]:
                fun = n[1]["label"].split("Fun[")[1].split("]")[0]
                # replace_node(ddg, n[0], fun)
                # ddg.nodes[fun]["type"] = 'function'
                ddg.nodes[n[0]]["type"] = 'function'
            elif "{fun: " in n[1]["label"]:
                label = n[1]["label"]
                # if any(skip in label for skip in skip_nodes):
                #     continue
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]
                # replace_node(ddg, n[0], fun)
                # ddg.nodes[fun]["type"] = 'function'
                ddg.nodes[n[0]]["type"] = 'function'

    # for n in list(ddg.nodes(data=True)):
    #      if ("label" in n[1]):
    #          if "AddrVFGNode" in n[1]["label"] and 'GlobalValVar' in n[1]["label"]:
    #             # from IPython import embed; embed()
    #             for func in ddg.successors(n[0]):
    #                 print(ddg.nodes[func]["label"] + " affects " + n[0])

    # dump_subgraph_a1(ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_old_ddg")
    new_ddg = nx.DiGraph()
    globals = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'global']
    functions = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'function']

    # noalias_map, union_pts = compute_noalias_alias_map(WPA_BIN, BC_FILE, IGNORE_FILE, NOALIAS_FILE)

    # for g in globals:
    #     new_ddg.add_node( ,**ddg.nodes[old_node])

    # new_ddg.add_nodes_from(globals)
    # new_ddg.add_nodes_from(functions)

    # Remove MSSA nodes based on points-to info


    ignore_symbols = [
            "HAL_USART_TransmitReceive_DMA",
            "HAL_USART_DMAStop",
            "HAL_USART_Abort",
            "DMA_CalcBaseAndBitshift",
            "HAL_DMA_DeInit",
            "HAL_USART_Receive_DMA"
                ]

    # from IPython import embed; embed()
    control_var2 = True
    m=1
    for g in globals:
        # add new global variable
        new_node_name = g[1]["label"].split('@')[1].split(' ')[0]

        new_ddg.add_node(new_node_name, **ddg.nodes[g[0]])

        # if new_node_name in ignore_symbols:
        #     from IPython import embed; embed()

        # from IPython import embed; embed()
        # if "AHBPrescTable" in g[1]["label"]:
        #     if control_var2:
        #         # from IPython import embed; embed()
        #         reachable = nx.descendants(ddg, g[0])
        #         reachable.add(g[0])
        #         sub = ddg.subgraph(reachable).copy()
        #         from networkx.drawing.nx_agraph import write_dot
        #         name = str(m) + "gAHBPrescTable.dot" 
        #         write_dot(sub, name)
        #         m=m+1
        #         print("found the variable AHBPrescTable in g")

        reachable = nx.descendants(ddg, g[0])

        # sub = ddg.subgraph(reachable).copy()

        # if "global_network" in g[1]["label"]:
        #     for n in reachable:
        #         print(ddg.nodes[n])
            
        #     print('found global variable')
        #     from IPython import embed; embed()

        # if new_node_name == "interpreter_temperature_model":
        #     from IPython import embed; embed()

        # if "interpreter_temperature_model" in g[1]["label"]:
        #     print("debug func")
        #     for n in reachable:
        #         from IPython import embed; embed()
        #         print(ddg.nodes[n])
        #     from IPython import embed; embed()

        _debug_targets = (
            "modelA",
            "arenaA",
            "labelsA",
            "modelB",
            "arenaB",
            "labelsB",
            "g_hello_world_int8_model_data",
        )
        debug_this_global = new_node_name in ("interpreter_temperature_model", "interpreter_second_temperature_model")
        if any(t in new_node_name for t in _debug_targets):
            reachable_funcs = [f for f in functions if f[0] in reachable]
            print(f"\n[globals_loop] raw_id='{g[0]}' -> new_node_name='{new_node_name}'")
            print(f"  ddg descendants: {len(reachable)}, function nodes reachable: {len(reachable_funcs)}")
            for f in reachable_funcs:
                print(f"    func: {fun_from_VFG_node(f[1])}")

        for f in functions:
            if f[0] in reachable:
                # from IPython import embed; embed()
                new_func_node_name = fun_from_VFG_node(f[1])

                # if new_func_node_name == "SkipFunc":
                #     continue

                if new_func_node_name is None:
                    print("Debug new_func_node_name is None")
                    print(f[1])

                if debug_this_global:
                    print(f"  [DDG] {new_node_name} -> {new_func_node_name}")
                    print(f"        node label: {f[1].get('label','')[:120]}")

                # pts = extract_pts_from_mssa_node(f)

                # if pts and new_func_node_name in noalias_map and any(p in union_pts for p in pts):
                #     print("Skipping: " + new_func_node_name)
                #     print(union_pts)
                #     print(pts)
                #     continue
                    # from IPython import embed; embed()

                # if "__cxx_global_var_init" in new_func_node_name:
                #     print("Ignorng auto generated global variable in VFG: " + new_func_node_name)
                if new_func_node_name not in new_ddg.nodes:
                    new_ddg.add_node(new_func_node_name, **ddg.nodes[f[0]])

                new_ddg.add_edge(new_node_name, new_func_node_name)

        # if new_node_name == "interpreter_temperature_model":
        #     from IPython import embed; embed()

        # Hack
        # for f in glob_lib_functions:
        #     # print("debug list")
        #     # embed()
        #     for n in reachable:
        #         if "GepVFGNode" in ddg.nodes[n]['label'] or "StoreVFGNode" in ddg.nodes[n]['label'] or "AddrVFGNode" in ddg.nodes[n]['label']:
        #             if f in ddg.nodes[n]['label']:
        #                 if f not in new_ddg.nodes:
        #                     new_ddg.add_node(f)
        #                 new_ddg.add_edge(new_node_name, f)

            # if f in reachable:
            #     # from IPython import embed; embed()
            #     new_func_node_name = fun_from_VFG_node(f[1])
            #     if "__cxx_global_var_init" in new_func_node_name:
            #         print("Ignorng auto generated global variable in VFG: " + new_func_node_name)
            #     # print(f[0])
            #     # print(new_func_node_name)
            #     # print(f[1])
            #     # print("\n")
            #     # from IPython import embed; embed()
            #     if new_func_node_name not in new_ddg.nodes:
            #         new_ddg.add_node(new_func_node_name, **ddg.nodes[f[0]])
                    
            #         # if new_func_node_name in ignore_symbols:
            #         #     from IPython import embed; embed()

            #     new_ddg.add_edge(new_node_name, new_func_node_name)

            # glob_lib_functions
            # for n in reachable:
            #     if "GepVFGNode" in ddg.nodes[n]['label'] or "StoreVFGNode" in ddg.nodes[n]['label']:
            #         new_func_node_name_ = fun_from_VFG_node(f[1])
            #         # if 'dense' in new_func_node_name_:
            #         #     print("found forward_dense")
            #         #     from IPython import embed; embed()
            #         # if 'forward_dense' == new_func_node_name_:
            #         #     print("found forward_dense")
            #         #     from IPython import embed; embed()
            #         if new_func_node_name_ in ddg.nodes[n]:
            #             if new_func_node_name_ not in new_ddg.nodes:
            #                 new_ddg.add_node(new_func_node_name_, **ddg.nodes[f[0]])

            #         new_ddg.add_edge(new_node_name, new_func_node_name_)
                # print(ddg.nodes[n])
            # from IPython import embed; embed()
            
    #for f1 in functions: // this isn't really the job of the ddg
    #    reachable = nx.descendants(ddg, f1[0])
    #    for f2 in functions:
    #        if f2[0] in reachable:
    #            new_ddg.add_edge(f1[0], f2[0])

    _confidential_names = [
        "modelA",
        "arenaA",
        "labelsA",
        "modelB",
        "arenaB",
        "labelsB",
        "g_hello_world_int8_model_data",
    ]

    def _dump_desc(graph, step_label):
        print(f"\n{'='*10} {step_label} {'='*10}")
        for _c in _confidential_names:
            # find the actual node — may have trailing ) or , due to parsing
            actual = _c if _c in graph.nodes else next(
                (n for n in graph.nodes if n.startswith(_c)), None)
            if actual is None:
                print(f"  {_c}: NOT in graph")
                continue
            desc = set(nx.descendants(graph, actual))
            print(f"  {_c} (node='{actual}', {len(desc)} descendants):")
            for d in sorted(desc):
                print(f"    {d}")

    _dump_desc(new_ddg, "AFTER globals loop (SVFG reachability edges)")

    # === Alias-aware seed expansion ===
    # For globals that ended up with no PDDG successors (no reachable function
    # nodes in the SVFG), check whether any other global's SVFG label contains
    # a pointer reference to them (i.e., `@<name>`).  If so, inherit those
    # globals' successors.  This handles constants that are only reachable at
    # runtime through a descriptor/wrapper struct (e.g. a weights array whose
    # address is stored as a compile-time constant in a data-map struct).
    _no_succ = [n for n in new_ddg.nodes
                if new_ddg.nodes[n].get('type') == 'global'
                and new_ddg.out_degree(n) == 0]
    for _empty in _no_succ:
        _pat = re.compile(r'@' + re.escape(_empty) + r'\b')
        for _ref_name, _ref_attrs in list(new_ddg.nodes(data=True)):
            if _ref_attrs.get('type') != 'global' or _ref_name == _empty:
                continue
            if _pat.search(_ref_attrs.get('label', '')):
                _inherited = list(new_ddg.successors(_ref_name))
                for _succ in _inherited:
                    new_ddg.add_edge(_empty, _succ)
                if _inherited:
                    print(f"[alias-expand] '{_empty}' had 0 PDDG successors; "
                          f"inherited {len(_inherited)} from '{_ref_name}'")

    # from IPython import embed; embed()
    # dump_subgraph_a1(new_ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_new_ddg")

    _alloc = "_ZN6tflite16MicroInterpreter15AllocateTensorsEv"


    if _alloc in new_ddg.nodes:
        print(f"\n[before potential_links] successors of AllocateTensors:")
        for s in new_ddg.successors(_alloc):
            print(f"  -> {s}")

    _dump_desc(new_ddg, "BEFORE potential_links")

    _confidential = [
        "modelA",
        "arenaA",
        "labelsA",
        "modelB",
        "arenaB",
        "labelsB",
        "g_hello_world_int8_model_data",
    ]
    _before_desc = {}
    for _c in _confidential:
        if _c in new_ddg.nodes:
            _before_desc[_c] = set(nx.descendants(new_ddg, _c))

    for link in potential_links:
        src, dst = link[0], link[1]
        if src not in new_ddg.nodes:
            continue
        if 'llvm.dbg' in src or 'llvm.dbg' in dst:
            continue
        dst_type = new_ddg.nodes[dst].get('type') if dst in new_ddg.nodes else None
        if dst_type == 'global':
            continue
        new_ddg.add_edge(src, dst)

    print("\n[potential_links] direct successor diff + entry-point links per confidential var:")
    for _c in _confidential:
        if _c not in new_ddg.nodes:
            print(f"  {_c}: NOT in new_ddg")
            continue
        _before_all  = _before_desc.get(_c, set())
        _after_all   = set(nx.descendants(new_ddg, _c))
        _added_all   = _after_all - _before_all

        _before_succ = set(new_ddg.successors(_c))

        print(f"\n  === {_c} ===")
        print(f"  DIRECT SUCCESSORS ({len(_before_succ)}): {sorted(_before_succ)}")
        print(f"  TOTAL added transitively: {len(_added_all)}")

        # Which potential_links used a before-reachable node as src and added a new dst?
        _entry_links = [
            (src, dst) for src, dst in potential_links
            if (src == _c or src in _before_all) and dst in _added_all
        ]
        if _entry_links:
            print(f"  ENTRY-POINT LINKS ({len(_entry_links)}):")
            for src, dst in sorted(_entry_links):
                src_t = new_ddg.nodes[src].get('type', '?') if src in new_ddg.nodes else '?'
                dst_t = new_ddg.nodes[dst].get('type', '?') if dst in new_ddg.nodes else '?'
                print(f"    [{src_t}] {src}  ->  [{dst_t}] {dst}")
        else:
            print(f"  ENTRY-POINT LINKS: none")

    if _alloc in new_ddg.nodes:
        print(f"\n[after potential_links] successors of AllocateTensors:")
        for s in new_ddg.successors(_alloc):
            print(f"  -> {s}")

    for interp in ("interpreter_temperature_model", "interpreter_second_temperature_model"):
        if interp in new_ddg.nodes:
            print(f"\n[after potential_links] Out-edges of {interp}:")
            for succ in new_ddg.successors(interp):
                print(f"  -> {succ}")

    for node in list(new_ddg.nodes(data=True)):
        if ("label" in node[1]):
            if "AddrVFGNode" in node[1]["label"] and 'GlobalValVar' in node[1]["label"]:
                data = node[1]["label"].split('@')[1].split(' ')[0]
                node[1]["name"] = data
            elif any(sub in node[1]["label"] for sub in ["FormalParmVFGNode", "FormalRetVFGNode"]) and "Fun[" in node[1]["label"]:
                fun = node[1]["label"].split("Fun[")[1].split("]")[0]
                node[1]["name"] = fun
            elif "{fun: " in node[1]["label"]:
                fun = node[1]["label"].split('{fun: ')[1].split('\\')[0]
                node[1]["name"] = fun
            else:
                print("Invalid node")
                print(node[1]["label"])
                print("\n")
        else:
            pass  # print("Invalid label node")
            # print(node[1])
            # print("\n")

    for interp in ("interpreter_temperature_model", "interpreter_second_temperature_model"):
        if interp in new_ddg.nodes:
            print(f"\n[after node naming] Out-edges of {interp}:")
            for succ in new_ddg.successors(interp):
                print(f"  -> {succ}")

    _dump_desc(new_ddg, "AFTER potential_links + node naming (final)")

    # dump_subgraph_a2(new_ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_pot_ddg")

    # for node in list(new_ddg.nodes(data=True)):
    #     node_type =  ddg.nodes[n[0]]["type"]
    #     node_name = node[1]["name"]
    #     print(node_type)
    #     print(node_name)

    # from IPython import embed; embed()
    return new_ddg

def get_node_kind(label):
    return label.split()[0].lstrip('{') 

from collections import Counter

import re

def extract_fun(label):
    return label.split('{fun: ')[1].split('\\')[0]

def extract_callee(label):
    m = re.search(r'@(.*?)\(', label)
    return m.group(1) if m else None

def print_func_node_info(graph):

    for n in graph.nodes(data=True):
        if ("label" in n[1]):        
            if "{fun: " in n[1]["label"]:
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]

                label = n[1]["label"]
                if label:
                    kind = get_node_kind(label)
                    node_type = kind
                    
                    if node_type in ("ActualINSVFGNode", "ActualOUTSVFGNode"):
                        caller = extract_fun(label)
                        callee = extract_callee(label)
                        print("Node: " + node_type)
                        print("caller: " + caller)
                        print("callee: " + callee)
                        continue
                    elif node_type in ("FormalINSVFGNode", "FormalOUTSVFGNode"):
                        callee = extract_fun(label)
                        print("Node: " + node_type)
                        print("callee: " + callee)
                        continue
                    elif node_type == "IntraMSSAPHISVFGNode":
                        fun = extract_fun(label)
                        print("Node: " + node_type)
                        print("fun: " + fun)
                        continue

def fun_from_VFG_node(node):
    if ("label" in node):
        # print(node)
        if "AddrVFGNode" in node["label"] and 'FunValVar' in node["label"]:
            data = node["label"].split("\\n")[-1].rstrip("}")
            # print("Returning " + data)
            # embed()
            return data
        # elif "ActualRetVFGNode" in node["label"]:
        #     match = re.search(r'call\s+[^\@]*@([^(]+)', node["label"])
        #     func_name = match.group(1).strip()
        #     # print ("===============" + func_name + "===============")
        #     return func_name

        # elif "IntraPHIVFGNode" in node["label"]:
        #     pattern = r'call\s+[^@]*@([^(]+)'
        #     label = node["label"]
        #     matches = re.findall(pattern, label)

        #     print ("===============", matches[0], "===============")
        #     return matches[0]
        elif "{fun: " in node["label"] or "Fun[" in node["label"]:
            label = node["label"]
            if label:
                kind = get_node_kind(label)
                node_type = kind
                # print(label)
                # print(node_type)

                if node_type in ("ActualINSVFGNode", "ActualOUTSVFGNode"):
                    callee = extract_callee(label)
                    return callee
                elif node_type in ("FormalINSVFGNode", "FormalOUTSVFGNode"):
                    callee = extract_fun(label)
                    return callee
                elif node_type == "IntraMSSAPHISVFGNode":
                    fun = extract_fun(label)
                    return fun
                elif node_type in ("FormalParmVFGNode", "FormalRetVFGNode"):
                    # from IPython import embed; embed()
                    fun = label.split("Fun[")[1].split("]")[0]
                    return fun
                elif node_type == "ActualParmVFGNode":
                    # global used as argument at a call site — containing function is the dependency
                    fun = extract_fun(label)
                    return fun



def load_ddg_svf_old(bc):
    node_kinds = Counter()
    seen = set()
    # first, generate the different maps
    cmd = [os.environ["SVF_BIN"] + "/svf-pieces", f'bc={bc}', '-ffmap', '-use-def', "-get-threads"]
    subprocess.run(cmd)

    # embed()
    path = "/home/hzm5471/repos/SVF/pieces/svfg_graph_for_pieces.dot"
    # path = "/home/hzm5471/repos/SVF/Debug-build/pieces_test/bak/svfg_final_dot"
    # cmd = [os.environ["SVF"], bc, "-dump-vfg", "-get-threads"]
    # subprocess.run(cmd, stdout=subprocess.DEVNULL)

    # cmd = ["cp", "./svfg_final_dot", path]
    # subprocess.run(cmd)

    # cmd = ["rm", "./svfg_final_dot"]
    # subprocess.run(cmd)
    
    ddg = read_dot(path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)

    potential_links = []
    for n in list(ddg.nodes(data=True)):
        name = n[0]
        if ':' in name:
            name = name.split(':')[0]
            replace_node(ddg, n[0], name)
    
    count = 0
    num=1
    control_var1 = True

    # dump_subgraph(ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_orig_ddg")

    for n in list(ddg.nodes(data=True)):
        # if "AHBPrescTable" in n[1]["label"]:
        if "_ZN6tflite26kFullyConnectedInputTensorE" in n[1]["label"]:
            if control_var1:
                reachable = nx.descendants(ddg, n[0])
                reachable.add(n[0])
                sub = ddg.subgraph(reachable).copy()
                from networkx.drawing.nx_agraph import write_dot
                name = str(num) + "_ZN6tflite26kFullyConnectedInputTensorE.dot"
                # from IPython import embed; embed()
                write_dot(sub, name)
                num=num+1
                print("found the variable _ZN6tflite26kFullyConnectedInputTensorE in n")
                # from IPython import embed; embed()
        if ("label" in n[1]):
            if "AddrVFGNode" in n[1]["label"] and 'GlobalValVar' in n[1]["label"]:
                data = n[1]["label"].split('@')[1].split(' ')[0]
                # from IPython import embed; embed()
                replace_node(ddg, n[0], data)
                ddg.nodes[data]["type"] = 'global'
            elif "IntraPHIVFGNode" in n[1]["label"]:
                spos = n[1]["label"].find("@")
                lpos = n[1]["label"].find("%")
                if (not spos == -1) and (spos < lpos or lpos == -1):
                    symbols = n[1]["label"].split("@")
                    try:
                        fun = symbols[1].split('(')[0]
                    except:
                        print(n[1]["label"])
                        exit()
                    for i in range(2, len(symbols)):
                        ref = symbols[i].split(',')[0]
                        if '(' in ref:
                            ref = ref.split('(')[0]
                        potential_links += [(ref, fun)]
            elif "ActualRetVFGNode" in n[1]["label"]:
                continue
                if not "@" in n[1]["label"]:
                    continue
                fun = n[1]["label"].split("@")[1].split("(")[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
            elif any(sub in n[1]["label"] for sub in ["FormalParmVFGNode", "FormalRetVFGNode"]) and "Fun[" in n[1]["label"]:
                fun = n[1]["label"].split("Fun[")[1].split("]")[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
            elif "{fun: " in n[1]["label"]:
                count = count+1
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]

                label = n[1]["label"]
                if label:
                    kind = get_node_kind(label)
                    node_type = kind
                    node_kinds[kind] += 1

                    if kind not in seen:
                        print("\n=== {} ===".format(kind))
                        print(label)
                        seen.add(kind)
                    
                    # ---- ACTUAL nodes (caller → callee) ----
                    # if node_type in ("ActualINSVFGNode", "ActualOUTSVFGNode"):
                    if node_type in ("ActualINSVFGNode"):
                        # continue
                        caller = extract_fun(label)
                        callee = extract_callee(label)
                        replace_node(ddg, n[0], callee)
                        ddg.nodes[callee]["type"] = 'function'
                        # ddg.nodes[n[0]]["type"] = 'function'
                        continue
                        # print("caller: " + caller)
                        # print("callee: " + callee)
                    # elif node_type in ("FormalINSVFGNode", "FormalOUTSVFGNode"):
                    elif node_type in ("FormalINSVFGNode"):
                        callee = extract_fun(label)
                        replace_node(ddg, n[0], callee)
                        ddg.nodes[callee]["type"] = 'function'
                        # ddg.nodes[n[0]]["type"] = 'function'
                        continue
                        # print("callee: " + callee)

                    elif node_type == "IntraMSSAPHISVFGNode":
                        fun = extract_fun(label)
                        # replace_node(ddg, n[0], fun)
                        # ddg.nodes[fun]["type"] = 'function'
                        # ddg.nodes[n[0]]["type"] = 'function'
                        continue
                        # print("fun: " + callee)


                # from IPython import embed; embed()
                # print(n[1])
                # print(fun)
                # replace_node(ddg, n[0], fun)
                # ddg.nodes[fun]["type"] = 'function'
                # ddg.nodes[n[0]]["type"] = 'function'
                # count = count+1

    for k, v in node_kinds.items():
        print(k, v)

    # dump_subgraph(ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_old_ddg")

    new_ddg = nx.DiGraph()
    globals = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'global']
    functions = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'function']
    
    # from IPython import embed; embed()
    new_ddg.add_nodes_from(globals)
    new_ddg.add_nodes_from(functions)

    print(count)
    # from IPython import embed; embed()

    control_var2 = True
    m=1
    for g in globals:
        # if "AHBPrescTable" in g[1]["label"]:
        #     if control_var2:
        #         # from IPython import embed; embed()
        #         reachable = nx.descendants(ddg, g[0])
        #         reachable.add(g[0])
        #         sub = ddg.subgraph(reachable).copy()
        #         from networkx.drawing.nx_agraph import write_dot
        #         name = str(m) + "gAHBPrescTable.dot" 
        #         write_dot(sub, name)
        #         m=m+1
        #         print("found the variable AHBPrescTable in g")
        reachable = nx.descendants(ddg, g[0])
        for f in functions:
            if f[0] in reachable:
                new_ddg.add_edge(g[0], f[0])
    #for f1 in functions: // this isn't really the job of the ddg
    #    reachable = nx.descendants(ddg, f1[0])
    #    for f2 in functions:
    #        if f2[0] in reachable:
    #            new_ddg.add_edge(f1[0], f2[0])

    # dump_subgraph(ddg, "AHBPrescTable", "_old_ddg")
    # dump_subgraph(new_ddg, "AHBPrescTable", "_new_ddg")

    # dump_subgraph(new_ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_new_ddg")


    for link in potential_links:
        if link[0] in new_ddg.nodes:# and new_ddg.nodes[link[0]]['type'] == 'global':
            new_ddg.add_edge(link[0], link[1])
    
    # dump_subgraph(new_ddg, "AHBPrescTable", "_pot_ddg")
    # dump_subgraph(new_ddg, "_ZN6tflite26kFullyConnectedInputTensorE", "_pot_ddg")

    return new_ddg

def load_cfg(bc):
    global analysis

    level = int(os.environ['ANALYSIS_LEVEL'])
    # if level < 50: # do light analysis
    #     analysis.cfg = load_cfg_light(bc)
    # else: # do svf analysis
    #     analysis.cfg = load_cfg_svf(bc)
    analysis.cfg = load_cfg_light(bc)

def load_ddg(bc):
    global analysis

    level = int(os.environ['ANALYSIS_LEVEL'])
    if level < 50: # do light analysis
        analysis.pddg = load_ddg_light(bc)
    else: # do svf analysis
        # analysis.pddg = load_ddg_svf(bc)
        # analysis.pddg = load_ddg_svf_old(bc)
        analysis.pddg = load_ddg_svf_algo1(bc)
        
        # analysis.pddg = load_ddg_svf_orig(bc)

def generate_pdg(cfg, ddg):
    pdg = merge_graphs(ddg, cfg)

    #pydot_graph = convert_to_pydot_safe(pdg)
    #pydot_graph.write_raw("pdg_combined.dot")
    # from IPython import embed; embed()
    from networkx.drawing.nx_agraph import write_dot
    write_dot(pdg, "pdg_graph_dump.dot")

    return pdg

def load_ddg_svf_orig(bc):
    # first, generate the different maps
    # cmd = [os.environ["SVF_BIN"] + "/svf-pieces", f'bc={bc}', '-ffmap', '-use-def']
    # subprocess.run(cmd)

    path = "/home/hzm5471/repos/SVF/Debug-build/bin/svfg_graph_for_pieces.dot"
    # cmd = [os.environ["SVF"], bc, "-dump-vfg", "-get-threads"]
    # subprocess.run(cmd, stdout=subprocess.DEVNULL)

    # cmd = ["cp", "./svfg_final.dot", path]
    # subprocess.run(cmd)

    # cmd = ["rm", "./svfg_final.dot"]
    # subprocess.run(cmd)
    
    ddg = read_dot(path)
    # cmd = ["rm", path]
    # subprocess.run(cmd)

    potential_links = []
    for n in list(ddg.nodes(data=True)):
        name = n[0]
        if ':' in name:
            name = name.split(':')[0]
            replace_node(ddg, n[0], name)
    for n in list(ddg.nodes(data=True)):
        if ("label" in n[1]):
            if "AddrVFGNode" in n[1]["label"] and 'GlobalValVar' in n[1]["label"]:
                data = n[1]["label"].split('@')[1].split(' ')[0]
                replace_node(ddg, n[0], data)
                ddg.nodes[data]["type"] = 'global'
            elif "IntraPHIVFGNode" in n[1]["label"]:
                spos = n[1]["label"].find("@")
                lpos = n[1]["label"].find("%")
                if (not spos == -1) and (spos < lpos or lpos == -1):
                    symbols = n[1]["label"].split("@")
                    try:
                        fun = symbols[1].split('(')[0]
                    except:
                        print(n[1]["label"])
                        exit()
                    for i in range(2, len(symbols)):
                        ref = symbols[i].split(',')[0]
                        if '(' in ref:
                            ref = ref.split('(')[0]
                        potential_links += [(ref, fun)]
            elif "ActualRetVFGNode" in n[1]["label"]:
                continue
                if not "@" in n[1]["label"]:
                    continue
                fun = n[1]["label"].split("@")[1].split("(")[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
            elif any(sub in n[1]["label"] for sub in ["FormalParmVFGNode", "FormalRetVFGNode"]) and "Fun[" in n[1]["label"]:
                fun = n[1]["label"].split("Fun[")[1].split("]")[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
            elif "{fun: " in n[1]["label"]:
                fun = n[1]["label"].split('{fun: ')[1].split('\\')[0]
                replace_node(ddg, n[0], fun)
                ddg.nodes[fun]["type"] = 'function'
    
    print("load_ddg_svf_orig")
    # from IPython import embed; embed()

    new_ddg = nx.DiGraph()
    globals = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'global']
    functions = [(n, d) for n, d in ddg.nodes(data=True) if d.get("type") == 'function']

    new_ddg.add_nodes_from(globals)
    new_ddg.add_nodes_from(functions)

    for g in globals:
        reachable = nx.descendants(ddg, g[0])
        for f in functions:
            if f[0] in reachable:
                new_ddg.add_edge(g[0], f[0])
    #for f1 in functions: // this isn't really the job of the ddg
    #    reachable = nx.descendants(ddg, f1[0])
    #    for f2 in functions:
    #        if f2[0] in reachable:
    #            new_ddg.add_edge(f1[0], f2[0])
    for link in potential_links:
        if link[0] in new_ddg.nodes:# and new_ddg.nodes[link[0]]['type'] == 'global':
            new_ddg.add_edge(link[0], link[1])

    return new_ddg


def run_analysis(bc):
    global analysis

    now = datetime.now()
    print(now)
    print("load cfg start")

    # embed()
    load_cfg(bc)
    print("load cfg end")
    now = datetime.now()
    print(now)
    print("load svfg start")
    # embed()
    load_ddg(bc)
    print("load svfg end")
    now = datetime.now()
    print(now)
    print("load pdg start")
    # embed()
    analysis.pdg = generate_pdg(analysis.cfg, analysis.pddg)
    print("load pdg end")
    now = datetime.now()
    print(now)
    # embed()
    # write_dot(analysis.pdg, "gen2_pdg.gpickle")

    return analysis

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        dg = read_dot(sys.argv[1])
        cg = read_dot(sys.argv[2])

        print(dg.graph["graph"]["label"])
        print(cg.graph["graph"]["label"])

        pdg = merge_graphs(dg, cg)

        pdot_graph = convert_to_pydot_safe(pdg)
        pdot_graph.write_raw("pdg_combined.dot")

        print("✅ PDG written to: pdg_combined.dot")

