#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MultiExp IR node
"""
from ..node import Node, build_method
from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr
from itertools import count


class MultiExp(Node):
    """Class for multiexpressions. It's used to package
    multiple expressions as a single node. It's not
    kept in final IR.
    """

    no_id = True
    __pragma_groups__ = count()

    @staticmethod
    def reset():
        MultiExp.__pragma_groups__ = count()

    def __init__(self, expressions: list[Node], location: str):
        super().__init__(location)
        self.expressions = expressions
        self.nodes = []
        self.edges = []
        self.out_ports = []
        self.pragmas = []

    def set_pragmas(self, pragmas):
        self.pragmas = pragmas

    def num_expressions(self):
        """Returns number of expressions"""
        return len(self.expressions)

    def num_out_ports(self):
        """Returns number of output ports"""
        return sum(map(lambda x: x.num_out_ports(), self.expressions))

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Build contained expressions and pass their outputs
        to parent node"""

        # split target ports to spread them around corresponding child nodes
        # example: (3 output ports and 2 expressions, exp1 has 2 output ports
        # and exp2 has 1
        # ports: |p1 |p2 |  p3  |
        # exps:  \ exp1 / \exp2/
        port_index = 0

        if self.pragmas:
            pragmas_id = next(MultiExp.__pragma_groups__)

        for n, exp in enumerate(self.expressions):
            if self.pragmas:
                exp.pragmas = self.pragmas
                exp.pragma_group = pragmas_id

            length = exp.num_out_ports()
            self.add_sub_ir(
                exp.build(target_ports[port_index: port_index + length], scope)
            )
            port_index += length

        return SubIr(self.nodes, self.edges, [])
