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
from ..type import IntegerType


class ArrayAccess(Node):

    def __init__(self, array: Node, index: Node, location: str = None):
        super().__init__(location)
        self.array = array
        self.index = index
        self.name = "ArrayAccess"

    def num_out_ports(self) -> int:
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:

        self.in_ports = [
                         Port(self.id, IntegerType(), 0),  # Array
                         Port(self.id, IntegerType(self.location), 1),  # Index
                         ]

        identifier_ir = self.array.build([self.in_ports[0]], scope)

        self.out_ports = [Port(self.id, None, 0)]
        # print(self.index[0])
        indices_ir = [index.build([self.in_ports[1]], scope) for index in self.index]

        del self.array
        del self.index

        return (SubIr(nodes=[self], output_edges=[], internal_edges=[]) +
                identifier_ir +
                index_ir)
