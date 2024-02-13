#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
If IR node
"""
from __future__ import annotations

from ..node import Node, build_method

from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr
from .multi_exp import MultiExp
from ..type import BooleanType


class Branch(Node):
    """Handles if's branches"""

    def __init__(self, body: MultiExp, name: str = "ElseIf"):
        """Condition node"""
        super().__init__(body.location)
        self.body = body
        self.name = name

    def build(self, scope: SisalScope) -> SubIr:
        """Convert parsed data to IR"""
        self.copy_ports(scope.node)
        scope = SisalScope(self)
        self.add_sub_ir(self.body.build(self.out_ports, scope))
        del self.body

    def num_out_ports(self):
        return self.body.num_out_ports()

    def num_in_ports(self):
        return self.body.num_in_ports()


class Condition(Node):
    """Handles if's condition"""

    def __init__(self, conditions: MultiExp):
        """Condition node"""
        super().__init__(conditions.location)
        self.conditions = conditions
        self.name = "Condition"

    def build(self, scope: SisalScope) -> SubIr:
        """Convert parsed data to IR"""
        self.copy_ports(scope.node, out=False)
        self.out_ports = [
            Port(self.id, BooleanType(), index, "cond #" + str(index))
            for index in range(self.conditions.num_out_ports())
        ]
        scope = SisalScope(self)
        self.add_sub_ir(self.conditions.build(self.out_ports, scope))
        del self.conditions

    def num_out_ports(self):
        return self.conditions.num_out_ports()

    def num_in_ports(self):
        return self.conditions.num_in_ports()


class If(Node):
    """Class for Ifs"""

    connect_parent = True
    copy_scope_ports = True
    copy_target_ports = True

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
        self.branches = (
            [Branch(then_, "Then")]
            + [Branch(elseif, "ElseIf") for elseif in elseifs]
            + [Branch(else_, "Else")]
        )
        self.name = "If"

    def __repr__(self) -> str:
        return str(f"<If {self.location})>")

    def check_ports_consistency(self):
        num_out_ports = self.num_out_ports()
        # TODO check that types are the same also
        for branch in self.branches:
            if branch.num_out_ports() != num_out_ports:
                raise Exception(
                    f"Error: number of output ports should be equal "
                    f"in all branches of an 'if' ({self.location}) "
                    f"and equal to expected number of output ports."
                )

    def num_out_ports(self):
        n_then = self.branches[0].num_out_ports()
        return n_then

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Recursively rebuilds the if's ir into a dataflow graph"""
        scope = SisalScope(self)
        self.check_ports_consistency()
        self.condition.build(scope)
        for branch in self.branches:
            branch.build(scope)

        # TODO revisit this soultion, it's a semi-measure at this moment:
        for o_p, b_o_p in zip(self.out_ports, self.branches[0].out_ports):
            if not o_p.type:
                o_p.type = b_o_p.type

        return SubIr(nodes=[self], internal_edges=[], output_edges=[])

    def ir_(self) -> dict:
        """Returns this IF as a standard dictionary
        suitable for export"""
        retval = super().ir_()
        retval["branches"] = [branch.ir_() for branch in retval["branches"]]
        return retval

    def find_sub_node(self, type_: str) -> list:
        a = (
            self.condition.find_sub_node(type_)
        ) + [branch.find_sub_node(type_) for branch in self.branches]
        return a
