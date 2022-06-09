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
from ..type import IntegerType  # , ArrayType


class ArrayAccess(Node):

    def __init__(self, array: Node, index: Node, location: str = None):
        super().__init__(location)
        if array:
            self.array = array
        if index:
            self.index = index

        self.name = "ArrayAccess"

        self.in_ports = [
            Port(self.id, None, 0),  # the array, type is set later by Edge
            Port(self.id, IntegerType(), 1),  # element's index
        ]

        self.out_ports = [Port(self.id, None, 0)]

    def num_out_ports(self) -> int:
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:

        array_ir = self.array.build([self.in_ports[0]], scope)
        # TODO assert its actually an array and put out an error
        # if it isn't
        # TODO assert there is one edge in array_ir's output_edges

        self.out_ports[0].type = array_ir.output_type().element

        nodes = [self]
        indices_ir = SubIr([], [], [])
        edges = []

        self.in_ports[0].type = array_ir.output_type()

        for index in self.index[1:]:
            aa = ArrayAccess(None, None, self.location)
            prev_type = nodes[-1].out_ports[0].type
            aa.out_ports[0].type = (
                prev_type.element
                if hasattr(prev_type, "element") else prev_type
            )

            aa.in_ports[0].type = prev_type

            edges.append(Edge(nodes[-1].out_ports[0], aa.in_ports[0]))
            indices_ir += index.build([aa.in_ports[1]], scope)
            nodes.append(aa)

        del self.array
        del self.index

        return (
            SubIr(nodes=nodes, output_edges=[], internal_edges=edges)
            + array_ir
            + indices_ir
        )
