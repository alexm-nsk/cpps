#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Array access node
"""

from ..node import Node
from ..scope import SisalScope

# from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port
from ..edge import Edge
from ..type import IntegerType, ArrayType
from ..error import SisalError


class ArrayAccess(Node):

    """Array access node"""

    def __init__(self, array: Node, index: Node, location: str = None):
        super().__init__(location)
        self.name = "ArrayAccess"

        if array:
            self.array = array
        if index:
            self.index = index

        self.in_ports = [
            # the array, type is set later by Edge
            Port(self.id, None, 0, label="array"),
            # element's index
            Port(self.id, IntegerType(), 1, "index"),
        ]

        self.out_ports = [Port(self.id, None, 0)]

    def num_out_ports(self) -> int:
        return 1

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """ArrayAccess's build method
        note it's not decorated as build method because self isn't the
        output node and the decorator would connect that to the output"""

        # TODO put self at the end and return the decorator (don't forget to
        # remove the output edge

        # check if number of outputs matches the expected number
        # this would have been done by the decorator
        if len(target_ports) != self.num_out_ports():
            raise SisalError(
                f"Error: {len(target_ports)} expressions expected,"
                f"got {len(self.expressions)} at {self.location}"
            )

        array_ir = self.array.build([self.in_ports[0]], scope)

        # check that array expression puts out exactly one value:
        if (len(array_ir.edges) != 1):
            raise SisalError("Expression must have exactly one output for "
                             "array access", self.location)

        # check if expression is an array
        if (type(array_ir.output_type()) != ArrayType):
            raise SisalError("Expression is not an array", self.location)

        # perform access' length check:
        if len(self.index) > array_ir.output_type().depth():
            raise SisalError("Number of array's dimensions is less than "
                             "the depth of array access.", self.location)

        # build the ArrayAccess chain:
        nodes = [self]
        edges = []
        self.out_ports[0].type = array_ir.output_type().element_type()
        indices_ir = self.index[0].build([self.in_ports[1]], scope)
        self.in_ports[0].type = array_ir.output_type()
        for index in self.index[1:]:
            aa = ArrayAccess(None, None, self.location)
            prev_type = nodes[-1].out_ports[0].port_type()
            aa.out_ports[0].type = (
                prev_type.element
                if hasattr(prev_type, "element") else prev_type
            )
            aa.in_ports[0].type = prev_type
            edges.append(Edge(nodes[-1].out_ports[0], aa.in_ports[0]))

            indices_ir += index.build([aa.in_ports[1]], scope)
            nodes.append(aa)

        # remove the no longer necessary fields:
        del self.array
        del self.index

        # make the final edge that puts out array's element
        output_edge = Edge(nodes[-1].out_ports[0], target_ports[0])
        return (
            SubIr(nodes, output_edges=[output_edge], internal_edges=edges)
            + array_ir
            + indices_ir
        )
