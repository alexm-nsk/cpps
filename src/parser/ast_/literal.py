#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Describes literals
"""

from ..node import Node, build_method
from ..port import Port
from ..type import Type
from ..scope import SisalScope
from ..sub_ir import SubIr


class Literal(Node):
    """Class for literal values"""

    def __init__(self, type_: Type, value=None, location: str = None):
        super().__init__(location)
        self.type = type_
        self.value = value
        self.name = "Literal"
        self.out_ports = [Port(self.id, self.type, index=0)]

    @build_method
    def build(self,
              target_ports: list[Port],
              scope: SisalScope = None) -> SubIr:
        return SubIr(nodes=[self], internal_edges=[], output_edges=[])

    def __repr__(self):
        # return str(self.ir_())
        return f"<Literal: {self.value}>"

    def ir_(self) -> dict:
        retval = super().ir_()
        del retval["type"]

        return retval
