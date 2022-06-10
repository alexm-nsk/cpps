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

# TODO add unwrapping the let


class Let(Node):

    copy_scope_ports = True

    def __init__(self, init: list[Statement], body: MultiExp,
                 location: str = None):
        super().__init__(location)
        self.name = "Let"
        self.init = init
        self.body = body

    def num_out_ports(self):
        return self.body.num_out_ports()

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:

        scope = SisalScope(self)
        # body = Node
        return SubIr([], [], [])
