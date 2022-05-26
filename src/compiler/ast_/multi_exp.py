#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function IR node
"""
from copy import deepcopy
from ..node import Node
from ..port import Port
from ..scope import SisalScope


class MultiExp(Node):
    """Class for multiexpressions"""

    no_id = True

    def __init__(self, expressions: list[Node], location: str):
        self.expressions = expressions
        super().__init__(location)

    def build(self, target_ports: list[Port], scope):
        """Build contained expressions and pass their outputs to
        parent node"""
        self.edges = []
        for out_port, out_node in zip(target_ports, self.expressions):
            built_data = out_node.build([out_port], scope)
            new_nodes += built_data.nodes
            self.edges += built_data.edges
        self.nodes = new_nodes
