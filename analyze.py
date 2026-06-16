from analyzer.gen_pdg import *
from dotenv import load_dotenv
from datetime import datetime


def run(bc):
    return run_analysis(bc)

def write_cfg_dot_streaming(cfg, path):
    with open(path, "w") as f:
        f.write("digraph CFG {\n")

        for n, attrs in cfg.nodes(data=True):
            label = attrs.get("label", str(n))
            f.write(f"\"{n}\" [label=\"{label}\"];\n")

        for u, v in cfg.edges():
            f.write(f"\"{u}\" -> \"{v}\";\n")

        f.write("}\n")


if __name__ == "__main__":
    load_dotenv()
    if len(sys.argv) >= 2:
        print("Run Analysis Start")
        now = datetime.now()
        print(now)
        analysis = run_analysis(sys.argv[1])
        print("Run Analysis End")
        now = datetime.now()
        print(now)
        sys.exit(0)

        print("cfg pydot start")
        pdot_graph = convert_to_pydot_safe(analysis.cfg)
        print("Writing pydot_safe output")
        now = datetime.now()
        print(now)
        # write_cfg_dot_streaming(analysis.cfg, "out/new_cfg.dot")
        # pdot_graph.write_raw("out/new_cfg.dot")
        print("cfg pydot end")
        now = datetime.now()
        print(now)

        print("svfg pydot start")
        # pdot_graph = convert_to_pydot_safe(analysis.pddg)
        print("Writing pydot_safe output")
        now = datetime.now()
        print(now)
        # write_cfg_dot_streaming(analysis.cfg, "out/new_pddg.dot")
        # pdot_graph.write_raw("out/pddg.dot")
        print("svfg pydot end")
        now = datetime.now()
        print(now)

        print("pdg pydot start")
        # pdot_graph = convert_to_pydot_safe(analysis.pdg)
        print("Writing pydot_safe output")
        now = datetime.now()
        print(now)
        # write_cfg_dot_streaming(analysis.cfg, "out/new_pdg.dot")
        # pdot_graph.write_raw("out/pdg.dot")
        print("pdg pydot end")
        now = datetime.now()
        print(now)