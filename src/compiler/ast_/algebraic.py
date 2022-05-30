#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Algebraic operations, bin node and various tools for those
"""

from ..node import Node
from ..port import Port
from ..edge import Edge
from ..type import IntegerType, RealType, BooleanType

# , BooleanType
from ..scope import SisalScope
from ..sub_ir import SubIr


class Bin(Node):
    """Binary operation node. Only processed within Algebraic's 'build'
    method"""

    alg_type_map = {
        "Integer": {"Real": RealType, "Integer": IntegerType},
        "Real": {"Real": RealType, "Integer": RealType},
    }

    def result_type(self):
        """Returns result type when processing two given types"""
        try:
            if self.operator in ["<", ">", ">=", "<="]:
                return BooleanType()
            left_name = self.in_ports[0].type.name
            right_name = self.in_ports[1].type.name
            return Bin.alg_type_map[left_name][right_name]()
        except KeyError:
            raise Exception(
                f"Operations {self.operator} between {left_name} and "
                f"{right_name} not implemented"
            )

    def __init__(self, operator: str, location: str):
        super().__init__(location)
        self.operator = operator
        self.in_ports = [
            Port(self.id, None, 0, "left"),  # port types will
            Port(self.id, None, 1, "right"),  # be set later
        ]

    def num_out_ports(self):
        """override Node's num_out_ports in case we don't have out_ports yet"""
        return 1

    def build(self, target_ports: list[Port], scope) -> SubIr:
        """returns an IR form of this node (Bin)"""
        out_type = self.result_type()
        self.out_ports = [
            Port(self.id, out_type, 0, f"binary output ({self.operator})")
        ]
        edge = Edge(self.out_ports[0], target_ports[0])
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

    def num_out_ports(self):
        """override Node's num_out_ports in case we don't have out_ports yet"""
        return 1

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Turn algebraic int nodes and edges"""
        # by design we get alternating operands and binary operators
        super().build(target_ports, scope)

        low_priority = ["+", "-"]

        def process(operators: list = []):
            """recursively processes parts of algebraic, until only single
            operands left"""
            for n, item in enumerate(self.expression):
                if type(item) == Bin and (
                    item.operator in operators or operators == []
                ):
                    left = self.expression[:n]
                    left = Algebraic(left) if len(left) > 1 else left[0]
                    right = self.expression[n + 1: ]
                    right = Algebraic(right) if len(right) > 1 else right[0]
                    # note the order of 'builds' in 'return':
                    # we first need to get left and right built,
                    # then we can set in-port types of bins
                    # the out-port types of left and right
                    return (
                        left.build([item.in_ports[0]], scope)
                        + right.build([item.in_ports[1]], scope)
                        + item.build([target_ports[0]], scope)
                    )

        return process(low_priority) or process()
