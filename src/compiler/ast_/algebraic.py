#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Algebraic operations, bin node and various tools for those
"""

from copy import deepcopy
from ..node import Node
from ..port import Port
from ..edge import Edge
from ..type import SingularType
from ..scope import SisalScope
from ..sub_ir import SubIr


class Bin(Node):
    """Binary operation node. Only processed within Algebraic's build"""

    def __init__(self, operator: str, location: str):
        super().__init__(location)
        self.operator = operator
        type_ = SingularType(name="integer")
        self.in_ports = [
            Port(self.id, type_, 0, "left"),
            Port(self.id, type_, 1, "right"),
        ]
        self.out_ports = [Port(self.id, type_, 0, "bin_output")]

    def build(self, target_port: Port, scope) -> SubIr:
        """returns an IR form of this node (Bin)"""
        edge = Edge(self.out_ports[0], target_port)
        return SubIr(nodes=[self], internal_edges=[], output_edges=[edge])

    def ir_(self):
        retval = super().ir_()
        return retval

    def __repr__(self):
        return f"<Bin: {self.operator}>"


class Algebraic(Node):
    """A class for algebraic calculations.
    Transforms into Bin and operand nodes"""

    no_id = True

    def __init__(self, expression: list, location: str = None):
        super().__init__(location)
        self.expression = expression

    def build(self, target_port: Port, scope: SisalScope) -> SubIr:
        """Turn algebraic int nodes and edges"""
        # by design we get alternating operands and binary operators
        print(self.expression)
        low_priority = ["+", "-"]
        for n, item in enumerate(self.expression):
            if type(item) == Bin and item.operator in low_priority:
                left = self.expression[:n]
                left = (
                    Algebraic(expression=left)
                    if len(left) > 1
                    else left[0]
                )
                right = self.expression[n + 1 :]
                right = (
                    Algebraic(expression=right)
                    if len(right) > 1
                    else right[0]
                )
                break
            return item.build(scope)
