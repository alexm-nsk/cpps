#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Init node (shared by Loop and Let)
"""

from ..node import Node, build_method
from ..port import Port
from ..type import IntegerType, RealType, BooleanType
from ..statement import Statement
from ..scope import SisalScope
from ..sub_ir import SubIr
from .multi_exp import MultiExp


class Let(Node):

    def __init__(self, init: list[Statement], body: MultiExp,
                 location: str = None):
        super().__init__(location)
        self.name = "Let"
        self.init = init
        self.body = body

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        pass
