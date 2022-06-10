#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Init node (shared by Loop and Let)
"""

from ..node import Node, build_method
from ..port import Port
from .multi_exp import MultiExp
from ..scope import SisalScope


class Init(Node):

    def __init__(self, statements: list, location: str = None):
        super().__init__(location)
        self.name = "Init"
        self.statements = statements

    def build(self, scope: SisalScope):
        self.copy_ports(scope.node, out=False)
        scope = SisalScope(self)

        del self.statements


class Body(Node):

    def __init__(self, expressions: MultiExp, location: str = None):
        super().__init__(location)
        self.name = "Body"
        self.expressions = expressions

    def build(self, scope: SisalScope):
        self.copy_ports(scope.node)
        scope = SisalScope(self)
        del self.expressions
