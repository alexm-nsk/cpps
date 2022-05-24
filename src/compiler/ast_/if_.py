#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
If IR node
"""
# from copy import deepcopy
from ..node import Node

# from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr


class If(Node):
    """Class for Ifs"""

    def __init__(
        self,
        condition: Node,
        then_: list[Node],
        elseifs: list[list[[Node]]],
        else_: list[Node],
        location: str = None,
    ):
        super().__init__(location)
        self.condition = condition
        self.then = then_
        self.elseifs = elseifs
        self.else_ = else_
        self.name = "If"

        self.build()

    def __repr__(self) -> str:
        return str(f"<If {self.location})>")

    def build(self, scope: SisalScope):
        """this recursively rebuilds the if's ir into a dataflow graph"""

    def ir_(self) -> dict:
        """This returns this if as a standard dictionary
        suitable for export"""
        retval = super().ir_(extra=["branches"])

        return retval
