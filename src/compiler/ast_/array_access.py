#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Array access node
"""

from ..node import Node, build_method
from ..scope import SisalScope

# from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port
from ..edge import Edge
from ..type import IntegerType, ArrayType


class ArrayAccess(Node):

    def __init__(self, array: Node, index: Node, location: str = None):
        super().__init__(location)
        if array:
            self.array = array
        if index:
            self.index = index

        self.name = "ArrayAccess"

        self.in_ports = [
            Port(self.id, ArrayType(element = IntegerType()), 0),  # addressed array, type is set later
            Port(self.id, IntegerType(), 1),  # element's index
        ]

        self.out_ports = [Port(self.id, IntegerType(), 0)]

    def num_out_ports(self) -> int:
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:

        array_ir = self.array.build([self.in_ports[0]], scope)

        nodes = [self]
        indices_ir = SubIr([], [], [])
        edges = []
        for index in self.index:
            aa = ArrayAccess(None, None, self.location)
            edges.append(Edge(nodes[-1].out_ports[0], aa.in_ports[0]))
            nodes.append(aa)
            indices_ir += index.build([aa.in_ports[1]], scope)

        del self.array
        del self.index

        return (
            SubIr(nodes=[self], output_edges=[], internal_edges=edges)
            + array_ir
            + indices_ir
        )
