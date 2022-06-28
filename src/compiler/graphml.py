#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graphml export
"""


class GraphMlModule:

    indent_str = "  "

    def __init__(self, module_data):
        self.module_data = module_data

    @staticmethod
    def indent(text, level=1):
        offset = GraphMlModule.indent_str * level
        return offset + text.replace("\n", "\n" + offset).rstrip()

    def key_str(key, value):
        return f'<data key="{key}">{value}</data>'

    def document(self):

        content = "\n".join(
            [function.graphml() for function in self.module_data["functions"]]
        )

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n\n'
            '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            '  xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n'
            '    http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n\n'
            '    <key id="type" for="node" attr.name="nodetype" '
            'attr.type="string"/>\n'
            '    <key id="location" for="node" attr.name="location" '
            'attr.type="string"/>\n\n'
            '    <graph id="module" edgedefault="directed">\n'
            f"{ self.indent(content, 4) }\n"
            "    </graph>"
            "\n\n</graphml>"
        )

    def __str__(self):
        return self.document()


def graphml(self, extra=""):
    """get gml text of ports, nodes, etc"""
    gml = GraphMlModule

    gml_content = ""

    # convert edges and nodes:

    for key in ["name", "function_name", "operator", "value"]:
        if key in self.__dict__:
            gml_content += gml.key_str(key, self.__dict__[key]) + "\n"

    # convert ports:
    if hasattr(self, "in_ports"):
        for i_p in self.in_ports:
            gml_content += i_p.graphml("in")
    gml_content += "\n"
    if hasattr(self, "out_ports"):
        for o_p in self.out_ports:
            gml_content += o_p.graphml("out")

    graph_content = ""

    for key in ["else", "elseif", "then", "condition",
                "body", "init", "returns", "range_gen",
                "reduction", "branches"]:
        if key in self.__dict__:
            if type(self.__dict__[key]) == list:
                for item in self.__dict__[key]:
                    graph_content += gml.indent(item.graphml()) + "\n"
            else:
                graph_content += gml.indent(self.__dict__[key].graphml()) + "\n"

    if hasattr(self, "nodes"):
        for node in self.nodes:
            graph_content += node.graphml() + "\n"

    if hasattr(self, "edges"):
        for edge in self.edges:
            graph_content += edge.gml() + "\n"

    if graph_content:
        graph = f'<graph id="{self.id}_graph" '\
                'edgedefault="directed">\n'
        graph += gml.indent(graph_content)
        graph += "\n</graph>"

        gml_content +="\n" + graph
    return f"<node id={self.id}>\n{gml.indent(gml_content)}\n</node>"
