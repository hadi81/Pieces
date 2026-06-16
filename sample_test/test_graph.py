import networkx as nx
from networkx.drawing.nx_agraph import write_dot
from networkx.drawing.nx_agraph import read_dot
from datetime import datetime
from IPython import embed

import re
import sys
import os

import subprocess


def dump_subgraph(ddg, node_name, subgraphname):
    
    for var in ddg.nodes(data=True):
        if node_name in var[0]:
            reachable = nx.descendants(ddg, var[0])
            reachable.add(var[0])
            sub = ddg.subgraph(reachable).copy()
            name = subgraphname+node_name
            write_dot(sub, name)
            break

def print_all_nodes(new_ddg, node_name):    

    for var in new_ddg.nodes(data=True):
        if node_name in var[0]:
            print(var)

def DFS(ddg, node_name, visited):
    if node_name in visited:
        return

    visited.add(node_name)
    # embed()
    print(ddg.nodes[node_name].get('label', '<no label>'))
    for succ in ddg.successors(node_name):
        DFS(ddg, succ, visited)


def load_ddg_svf_orig():
    path = "/home/hzm5471/repos/test/gen_graphs/samples/gep/svfg_graph_for_pieces.dot"

    ddg = read_dot(path)

    for n in list(ddg.nodes(data=True)):
        if 'label' in n[1]:
            if "AddrStmt" in n[1]['label'] and "%p =" in n[1]['label']:
                # reachable = nx.descendants(ddg, n[0])
                print(ddg.nodes[n[0]].get('label', '<no label>'))
                for succ in ddg.successors(n[0]):
                    # embed()
                    # print(ddg.nodes[succ].get('label', '<no label>')
                    visited = set()
                    DFS(ddg, succ, visited)
                    print("=======(DFS End)=======")
                    # embed()
                # break

if __name__ == "__main__":
    load_ddg_svf_orig()