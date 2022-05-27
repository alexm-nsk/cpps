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

    def num_out_ports(self):
        n_then = self.then.num_out_ports()
        n_else = self.else_.num_out_ports()
        num_elses_ports = [elseif.num_out_ports for elseif in self.elseifs]
        if n_then == n_else and \
           n_then.count(num_elses_ports) == len(num_elses_ports):
            raise Exception(
                f"number of expressions should be equal"
                f"in all branches of an 'if'{self.location}"
            )
        return len(self.then)

    def build(self, scope: SisalScope):
        """this recursively rebuilds the if's ir into a dataflow graph"""

    def ir_(self) -> dict:
        """Returns this IF as a standard dictionary
        suitable for export"""
        retval = super().ir_(extra=["branches"])

        return retval
