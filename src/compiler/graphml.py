#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graphml export
"""


class GraphMlModule:

    def document(content: str):
        return
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n\n'
        '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        '  xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n'
        '    http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n\n'
        '    <key id="type" for="node" attr.name="nodetype" attr.type="string"/>\n'
        '    <key id="location" for="node" attr.name="location" attr.type="string" />\n\n\n'
        f"  {content}s\n"
        "\n\n</graphml>"
