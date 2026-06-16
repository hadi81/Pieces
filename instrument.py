import os
import ast
import subprocess

def _cmap_from_policy(policy_file):
    """Parse a .policy file into a {function: compartment_id} dict.

    Each line is a Python list literal of function names belonging to that
    compartment (line 0 -> compartment 0, line 1 -> compartment 1, ...).
    """
    cmap = {}
    with open(policy_file) as f:
        for cid, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            functions = ast.literal_eval(line)
            for fn in functions:
                cmap[fn] = cid
    return cmap

def _cmap_from_firmware(firmware):
    """Build a {function: compartment_id} dict from firmware.compartmentMap."""
    cmap = {}
    compartmentIDs = {}
    for function in firmware.compartmentMap:
        compartment = firmware.compartmentMap[function]
        if compartment not in compartmentIDs:
            compartmentIDs[compartment] = len(compartmentIDs)
        cmap[function] = compartmentIDs[compartment]
    return cmap

def run(input, firmware, policy_file=None):
    if policy_file is not None:
        cmap = _cmap_from_policy(policy_file)
    else:
        cmap = _cmap_from_firmware(firmware)

    os.makedirs("./out", exist_ok=True)
    with open("./out/compartmentMap", 'w') as f:
        for function, cid in cmap.items():
            f.write(f'{function}\t{cid}\n')

    cmd = [os.environ["SVF_BIN"] + "/svf-pieces", f'bc={input["firmware"]["bc"]}', '-instrument']
    subprocess.run(cmd)
    subprocess.run(["llvm-dis-16", "temp.bc"])


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print(f"Usage: python instrument.py <bitcode.bc> <policy_file>")
        sys.exit(1)

    bc_path   = os.path.abspath(sys.argv[1])
    pol_path  = os.path.abspath(sys.argv[2])

    inp = {"firmware": {"bc": bc_path}}
    run(inp, firmware=None, policy_file=pol_path)
