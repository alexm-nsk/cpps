
@dataclass
class Edge:

    from_: Port
    to: Port



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

