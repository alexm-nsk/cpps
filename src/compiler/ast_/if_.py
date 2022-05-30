#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
If IR node
"""
from __future__ import annotations

# from copy import deepcopy
from ..node import Node

from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr
from .multi_exp import MultiExp
from ..type import BooleanType


class Branch(Node):
    """Handles if's branches"""


class Condition(Node):
    """Handles if's condition"""

    def __init__(self, conditions: MultiExp):
        """Condition node"""
        super().__init__(conditions.location)
        self.conditions = conditions

    def build(self, scope: SisalScope) -> SubIr:
        """ """
        self.copy_ports(scope, out=False)
        self.out_ports = [
            Port(self.id, BooleanType(), index, str(index))
            for index in range(self.conditions.num_out_ports())
        ]
        scope = SisalScope(self)
        self.conditions.build(self.out_ports, scope)


class If(Node):
    """Class for Ifs"""

    def __init__(
        self,
        condition: MultiExp,
        then_: MultiExp,
        elseifs: list[MultiExp],
        else_: MultiExp,
        location: str = None,
    ):
        super().__init__(location)
        self.condition = Condition(condition)
        self.then = then_
        self.elseifs = elseifs
        self.else_ = else_
        self.name = "If"

    def __repr__(self) -> str:
        return str(f"<If {self.location})>")

    def check_ports_consistency(self):
        n_then = self.then.num_out_ports()
        n_else = self.else_.num_out_ports()
        num_elses_ports = [elseif.num_out_ports for elseif in self.elseifs]
        if n_then != n_else or num_elses_ports.count(n_then) != len(num_elses_ports):
            raise Exception(
                f"Error: number of output ports should be equal "
                f"in all branches of an 'if' ({self.location}) "
                f"and equal to expected number of output ports."
            )

    def num_out_ports(self):
        n_then = self.then.num_out_ports()
        return n_then

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Recursively rebuilds the if's ir into a dataflow graph"""
        # TODO check that conditions put out a Boolean each
        super().build(target_ports, scope)
        self.condition.build(scope)
        return SubIr([], [], [])

    def ir_(self) -> dict:
        """Returns this IF as a standard dictionary
        suitable for export"""
        retval = super().ir_(extra=["branches"])

        return retval
