import re


def extract_pts_from_nodes(nodes):

    pts_pattern = re.compile(r'pts\{([^}]*)\}')
    fun_pattern = re.compile(r'\{fun:\s*([^}]+)\}')
    type_pattern = re.compile(r'\{([A-Za-z]+SVFGNode)')

    results = {}

    for node_id, attrs in nodes:

        label = attrs.get("label", "")

        node_type = None
        function = None
        pts = []

        # extract node type
        t = type_pattern.search(label)
        if t:
            node_type = t.group(1)

        # extract function
        f = fun_pattern.search(label)
        if f:
            function = f.group(1)

        # extract pts set
        p = pts_pattern.search(label)
        if p:
            values = p.group(1).split()
            for v in values:
                try:
                    pts.append(int(v))
                except ValueError:
                    pass

        results[node_id] = {
            "node_type": node_type,
            "function": function,
            "pts": pts
        }

    return results


def main():

    # Sample nodes exactly like SVFG nodes
    nodes = [

        ('Node0x5aedc694aae0',
         {'label': '{ActualINSVFGNode ID: 262946 at callsite: %call = call i32 @HAL_USART_Init(ptr noundef @husart1) {fun: MX_USART1_Init}CSMU(53017V_2)\\npts{225189 }'}),

        ('Node0x5aedc6226d40',
         {'label': '{FormalOUTSVFGNode ID: 246279 {fun: MX_USART2_Init}RETMU(41498V_2)\\npts{13 }'}),

        ('Node0x5aedc62269e0',
         {'label': '{FormalOUTSVFGNode ID: 246277 {fun: MX_USART2_Init}RETMU(52562V_2)\\npts{225211 }'}),

        ('Node0x5aedc69a2ab0',
         {'label': '{ActualINSVFGNode ID: 263613 {fun: MX_USART2_Init}CSMU(52562V_2)\\npts{225211 225222}'})
    ]

    info = extract_pts_from_nodes(nodes)

    print("\nParsed Results\n")

    for node, data in info.items():

        print(node)
        print("  type:", data["node_type"])
        print("  function:", data["function"])
        print("  pts:", data["pts"])
        print()


if __name__ == "__main__":
    main()
