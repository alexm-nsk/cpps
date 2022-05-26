#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Describes literals
"""

from ..node import Node
from ..port import Port
from ..type import Type
from ..scope import SisalScope
from ..sub_ir import SubIr
from ..edge import Edge


class Literal(Node):
    """Class for algebraic calculations transforms into Bin and
    operand nodes"""

    def __init__(self, type_: Type, value=None, location: str = None):
        super().__init__(location)
        self.type = type_
        self.value = int(value)
        self.name = "Literal"

    def build(self, target_ports: list[Port], scope: SisalScope = None) -> SubIr:
        """Turn literal into nodes and edges"""
        port = Port(self.id, self.type, index=0)
        self.out_ports = [port]
        output_edge = Edge(port, target_ports[0])
        return SubIr(nodes=[self], internal_edges=[], output_edges=[output_edge])

    def __repr__(self):
        # return str(self.ir_())
        return f"<Literal: {self.value}>"

    def ir_(self) -> dict:
        """Returns this function as a standard dictionary
        suitable for export"""
        retval = super().ir_()
        del retval["type"]

        return retval
