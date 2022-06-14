#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Init and Body nodes (shared by Loop and Let)
While they are inherited from Node class,
they don't have standard (i.e. decorated "build" methods)"""

from ..node import Node
from ..edge import Edge
from ..port import Port
from .multi_exp import MultiExp
from ..scope import SisalScope


class Init(Node):
    """Init node. Shared by let and loop"""

    def __init__(self, statements: list, location: str = None):
        super().__init__(location)
        self.name = "Init"
        self.statements = statements
        self.edges = []

    def build(self, scope: SisalScope):
        """ Build method. Note it's not standard, i.e.
        not using build_method-decorator."""
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
            # here we add newly defined value to the scope
            # so it's avalable to later init statements
            value_port = Edge.src_port(self.out_ports[index])
            # we find the port that puts out the defined value
            # and label it with identifier name
            # (so it can be found in the cope)
            value_port.label = definition.identifier.name
            scope.add_port(value_port)

        del self.statements


class Body(Node):
    """Body node. Shared by let and loop"""

    def __init__(self, expressions: MultiExp, location: str = None):
        super().__init__(location)
        self.name = "Body"
        self.expressions = expressions

    def build(self, init: Init,  scope: SisalScope):
        """ Build method. Note it's not standard, i.e.
        not using build_method-decorator and has init-node
        as an extra argument"""
        # copy ports from the scope:
        self.copy_ports(scope.node)
        # add ports corresponding to init's new values before
        # the port copied from the parent scope
        self.copy_results_ports(init)
        scope = SisalScope(self)
        self.add_sub_ir(self.expressions.build(self.out_ports, scope))
        del self.expressions
