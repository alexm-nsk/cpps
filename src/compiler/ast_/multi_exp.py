#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MultiExp IR node
"""
from ..node import Node
from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr


class MultiExp(Node):
    """Class for multiexpressions. It's used to package
    multiple expressions as a single node. It's not
    kept in final IR.
    """

    no_id = True

    def __init__(self, expressions: list[Node], location: str):
        super().__init__(location)
        self.expressions = expressions
        self.nodes = []
        self.edges = []

    @property
    def num_expressions(self):
        return len(self.expressions)

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Build contained expressions and pass their outputs
        to parent node"""

        if len(target_ports) != self.num_expressions:
            raise Exception(
                f"Error: {len(target_ports)} expressions expected,"
                f"got {len(self.expressions)} at {self.location}"
            )

        # split target ports to spread them around corresponging child nodes
        # example: (3 output ports and 2 expressions, exp1 has 2 output ports)
        # ports: |p1 |p2 |  p3  |
        # exps:  \ exp1 / \exp2/
        port_index = 0
        for n, exp in enumerate(self.expressions):
            length = exp.num_out_ports()
            self.add_sub_ir(
                exp.build(target_ports[port_index: port_index + length], scope)
            )
            port_index += length

        return SubIr(self.nodes, self.edges, [])
