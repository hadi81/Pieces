import ast
import subprocess
import re

def demangle(name):
    try:
        result = subprocess.run(['c++filt', name], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error demangling {name}: {e}"

def extract_lists_from_file(filepath):
    with open(filepath, 'r') as f:
        contents = f.read()

    # Find all list-like patterns
    list_pattern = re.findall(r'\[.*?\]', contents, re.DOTALL)

    parsed_lists = []
    for list_str in list_pattern:
        try:
            parsed = ast.literal_eval(list_str)
            if isinstance(parsed, list):
                parsed_lists.append(parsed)
        except (SyntaxError, ValueError):
            continue
    return parsed_lists

# === Main ===
input_file = '/home/hadi/repos/Pieces/partitioner/out/.policy'  # Update as needed
lists = extract_lists_from_file(input_file)

for idx, symbol_list in enumerate(lists, 1):
    print(f"\nList {idx} (size={len(symbol_list)}):")
    for symbol in symbol_list:
        print(f"{symbol} -> {demangle(symbol)}")
