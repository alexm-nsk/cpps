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
