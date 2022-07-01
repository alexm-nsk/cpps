from dataclasses import dataclass
from .ast_ import function, alg, common, function, if_, let, literal, loop
#from .node import Node

nodes = {}


class Type:
    def __init__(self, type_object):
        self.location = type_object["location"]
        if "name" in type_object:
            self.name = type_object["name"]
        else:
            self.element = Type(type_object["element"])
            self.multitype = type_object["multi_type"]


@dataclass
class Port:
    node_id: int
    type: Type
    index: int
    label: str


@dataclass
class Edge:

    from_: Port
    to: Port


def get_port(node_id, index):
    pass


def parse_edge(edge):
    if "from" in edge and "to" in edge:
        from_ = Port(edge["from"][0], None, edge["from"][1], None)
        to = Port(edge["to"][0], None, edge["to"][1], None)
        return Edge(from_, to)
    else:
        from_, to = (
            Port(
                node_id=edge[i]["node_id"],
                type=Type(edge[i]["type"]),
                index=edge[i]["index"],
                label=edge[i]["label"] if "label" in edge[i] else None,
            )
            for i in range(2)
        )
        return Edge(from_, to)


def parse_port(port):
    return Port(
        port["node_id"],
        Type(port["type"]),
        port["index"],
        port["label"] if "label" in port else None,
    )


def parse_node(node):
    nodes[node["id"]] = node
    node["in_ports"] = [parse_port(port) for port in node["in_ports"]]
    node["out_ports"] = [parse_port(port) for port in node["out_ports"]]
    # print(in_ports, out_ports)
    for edge in node["edges"]:
        parse_edge(edge)


def parse_ir(ir_data):
    for function in ir_data["functions"]:
        parse_node(function)
