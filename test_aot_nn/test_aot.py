import re
from collections import defaultdict


def parse_aot_nn_info(filename="aot_nn_info"):
    """
    Parse the LLVM-generated aot_nn_info file and return a dictionary:

    {
        "global_network": ["forward_dense", "forward_relu", ...],
        "gemm_0_layer": ["forward_dense"],
        ...
    }
    """

    result = defaultdict(list)

    current_network = None
    current_layer = None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            # Match network
            net_match = re.match(r"Network global: @(\S+)", line)
            if net_match:
                current_network = net_match.group(1)
                current_layer = None
                result.setdefault(current_network, [])
                continue

            # Match layer
            layer_match = re.match(r"Layer\[\d+\]: @(\S+)", line)
            if layer_match:
                current_layer = layer_match.group(1)
                result.setdefault(current_layer, [])
                continue

            # Match forward function
            forward_match = re.match(r"forward:\s*(\S+)", line)
            if forward_match:
                forward_fn = forward_match.group(1)

                if current_network:
                    result[current_network].append(forward_fn)

                if current_layer:
                    result[current_layer].append(forward_fn)

    return dict(result)


# --------------------------------------------------
# Test section (runs only if executed directly)
# --------------------------------------------------

if __name__ == "__main__":

    try:
        nn_dict = parse_aot_nn_info("/home/hzm5471/repos/SVF/Debug-build/wpa/aot_nn_info")

        print("Parsed Neural Network Info:\n")
        for key, value in nn_dict.items():
            print(f"{key}: {value}")

    except FileNotFoundError:
        print("Error: aot_nn_info file not found.")