#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Init node (shared by Loop and Let)
"""

from ..node import Node, build_method
from ..port import Port
from ..type import IntegerType, RealType, BooleanType

from ..scope import SisalScope
from ..sub_ir import SubIr


class Init(Node):

    def __init__(self, statements: list):
        self.name = "Init"
        self.statements = statements

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope):
        pass
