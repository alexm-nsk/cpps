#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Init and Body nodes (shared by Loop and Let)
While they are inherited from Node class,
they don't have standard (i.e. decorated "build" methods)"""

from ..node import Node
from ..port import Port
from .multi_exp import MultiExp
from ..scope import SisalScope


class Init(Node):
    def __init__(self, statements: list, location: str = None):
        super().__init__(location)
        self.name = "Init"
        self.statements = statements
        self.edges = []

    def build(self, scope: SisalScope):
        self.copy_ports(scope.node, out=False)

        self.out_ports = [
            Port(self.id, None, index, exp.identifier.name)
            for index, exp in enumerate(self.statements)
        ]

        scope = SisalScope(self)

        for index, definition in enumerate(self.statements):
            self.add_sub_ir(
                    definition.value.build([self.out_ports[index]], scope)
                    )

        del self.statements


class Body(Node):
    def __init__(self, expressions: MultiExp, location: str = None):
        super().__init__(location)
        self.name = "Body"
        self.expressions = expressions

    def build(self, scope: SisalScope):
        self.copy_ports(scope.node)
        scope = SisalScope(self)
        self.add_sub_ir(self.expressions.build(self.out_ports, scope))
        del self.expressions
