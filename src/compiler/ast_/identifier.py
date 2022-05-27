#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Identifier IR node
"""
from ..node import Node
from ..port import Port
from ..edge import Edge
from ..scope import SisalScope
from ..sub_ir import SubIr


class Identifier(Node):
    """This is an intermediate node, it's deleted in the second pass"""

    no_id = True

    def __init__(self, identifier_name, location: str = None):
        self.name = identifier_name
        super().__init__(location)

    def __repr__(self):
        return f"<Identifier: \"{self.name}\" {self.location}"

    def num_out_ports(self):
        """override Node's num_out_ports in case we don't have out_ports yet"""
        return 1

    def build(self, target_ports: list[Port], scope: SisalScope):
        edge = Edge(scope.resolve_by_name(self.name),
                    target_ports[0])

        return SubIr(nodes=[], output_edges=[edge], internal_edges=[])
