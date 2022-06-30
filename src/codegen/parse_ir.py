from dataclasses import dataclass


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


def parse_edge(edge):
    if "from" in edge and "to" in edge:
        return Edge(edge)
    else:
        from_ = dict(id=edge[0]["node_id"], port=edge[0]["index"])
        to = dict(id=edge[1]["node_id"], port=edge[1]["index"])
        return Edge(from_, to)


def parse_port(port):
    return Port(port["node_id"],
                Type(port["type"]),
                port["index"],
                port["label"] if "label" in port else None)


def parse_node(node):
    in_ports = [parse_port(port) for port in node["in_ports"]]
    out_ports = [parse_port(port) for port in node["out_ports"]]
    print(in_ports, out_ports)
    # for edge in node["edge"]:
    # print(edge)


def parse_ir(ir_data):
    for function in ir_data["functions"]:
        parse_node(function)
