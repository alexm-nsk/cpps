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

    @property
    def num_expressions(self):
        return len(self.expressions)

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Build contained expressions and pass their outputs
        to parent node"""
        self.nodes = []
        self.edges = []
        if len(target_ports) != self.num_expressions:
            raise Exception(
                f"{len(target_ports)} expressions expected"
                f"got {len(self.expressions)} at {self.location}"
            )

        for out_port, out_node in zip(target_ports, self.expressions):
            built_data = out_node.build([out_port], scope)
            self.add_sub_ir(built_data)

        return SubIr(self.nodes, self.edges, [])
