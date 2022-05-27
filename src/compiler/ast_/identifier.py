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
        super().__init__(location)
        self.name = identifier_name

    def __repr__(self):
        return f"<Identifier: \"{self.name}\" {self.location}"

    def num_out_ports(self):
        """override Node's num_out_ports because we don't need any ports"""
        return 1

    def build(self, target_ports: list[Port], scope: SisalScope):
        super().build(target_ports, scope)
        edge = Edge(scope.resolve_by_name(self.name),
                    target_ports[0])

        return SubIr(nodes=[], output_edges=[edge], internal_edges=[])
