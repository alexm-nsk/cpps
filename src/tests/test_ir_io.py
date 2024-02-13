import sys
import json
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from ir.module import Module
from ir.edge import Edge

M = Module("tests/array.json")

#M.delete_node(M.nodes["node4"], True)
#M.delete_node(M.nodes["node3"], True)
M.delete_node(M.nodes["node1"], True)

json_data = M.save_to_json()
output = json.dumps(json_data, indent=2)


print(M.functions["main"].out_ports[0].type.multi_type)
open("/home/alexm/output.json", "w").write(output)


# check if module json doesn't change when we load it and export it again:
M2 = Module("/home/alexm/output.json")


if output == json.dumps(M2.save_to_json(), indent=2):
    print("Invariant test passed: export is invariant")
else:
    print("Invariant test failed: export is different from import")

for name, node in sorted(M.nodes.items()):
    try:
        print(M.edges_from[node.out_ports[0].id])
    except:
        print(f"{node.id}({node.name}) ", "has no output edges")

import os
os.system("python sisal.py -i ../examples/array.sis --json")
