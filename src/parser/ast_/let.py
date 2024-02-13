#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Let node
"""

from ..node import Node, build_method
from ..port import Port
from ..statement import Statement
from ..scope import SisalScope
from ..sub_ir import SubIr
from .multi_exp import MultiExp
from .common import Init, Body

# TODO add unwrapping the let


class Let(Node):
    """ Let node. Uses Init and Body nodes"""

    copy_scope_ports = True
    copy_target_ports = True
    connect_parent = True

    def __init__(self, init: list[Statement], body: MultiExp,
                 location: str = None):
        super().__init__(location)
        self.name = "Let"
        self.init = init
        self.body = body

    def num_out_ports(self):
        return self.body.num_out_ports()

    def copy_port_types(self):
        for o_p, b_o_p in zip(self.out_ports, self.body.out_ports):
            o_p.type = b_o_p.type

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        scope = SisalScope(self)
        self.init = Init(self.init)
        self.init.build(scope)
        self.body = Body(self.body)
        self.body.build(self.init, scope)
        self.copy_port_types()
        return SubIr([self], [], [])

    def find_sub_node(self, type_: str) -> list:
        return (
            self.body.find_sub_node(type_)
            + self.init.find_sub_node(type_)
        )
