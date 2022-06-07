#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Array access node
"""

from ..node import Node, build_method
from ..scope import SisalScope
from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port
from ..type import IntegerType

class ArrayAccess(Node):

    def __init__(self, array_name, indices: list[Node],
                 location: str = None):
        super().__init__(location)
        self.array_name = array_name

    def num_out_ports(self):
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope):
        # port that corresponds to the array's variable
        print(scope.node.in_ports)
        identifier_port = scope.resolve_by_name(self.array_name.name)
        print(self.array_name)
        item_type = identifier_port.type.element

        self.out_ports = [Port(self.id, item_type, 0)]
        self.in_ports = [Port(self.id, IntegerType(self.location), 0),
                         Port(self.id, IntegerType(self.location), 1)]

        return SubIr(nodes=[], output_edges=[], internal_edges=[])
