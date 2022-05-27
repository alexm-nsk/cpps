#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
If IR node
"""
from __future__ import annotations
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
        then_: MultiExp,
        elseifs: list[MultiExp],
        else_: MultiExp,
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

    def num_out_ports(self):
        n_then = self.then.num_out_ports()
        n_else = self.else_.num_out_ports()
        num_elses_ports = [elseif.num_out_ports for elseif in self.elseifs]
        if n_then != n_else or \
           num_elses_ports.count(n_then) == len(num_elses_ports):
            raise Exception(
                f"Error: number of expressions should be equal "
                f"in all branches of an 'if' ({self.location}) "
                f"and equal to expected number of expressions."
            )
        return n_then

    def build(self, scope: SisalScope):
        """this recursively rebuilds the if's ir into a dataflow graph"""

    def ir_(self) -> dict:
        """Returns this IF as a standard dictionary
        suitable for export"""
        retval = super().ir_(extra=["branches"])

        return retval
