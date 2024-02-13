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
        not using @build_method decorator."""
        self.copy_ports(scope.node, out=False)

        self.out_ports = []

        for statement in self.statements:
            self.out_ports += [
                Port(self.id, None, len(self.out_ports)+index, identifier.name)
                for index, identifier in enumerate(statement.identifiers)
            ]

        scope = SisalScope(self)

        # got through definitions:
        # a, b := ...
        # c    := ...
        index = 0
        for definition in self.statements:
            # number of values defined in this statement:
            num_values = definition.values.num_out_ports()
            # build IR for definitions:
            self.add_sub_ir(
                    definition.values.build(
                        self.out_ports[index: index + num_values],
                        scope
                        )
                )
            # add newly defined values to the scope:
            for var_index, port in enumerate(self.out_ports[index: index + num_values]):
                # get the port from which the value comes
                value_port = Edge.src_port(port)
                # get the identifier corresponding to that port:
                identifier = definition.identifiers[var_index]
                # set port's location to identifiers location:
                value_port.type.location = identifier.location
                # add value to the scope so it's available to later definitions
                # like
                # a := 1
                # b := a + 1 (a needs to be in the scope)
                scope.add_new_value(identifier.name, value_port, check=True)

            index += num_values

        del self.statements


class Body(Node):
    """Body node. Used by let"""

    def __init__(self, expressions: MultiExp, location: str = None):
        super().__init__(location)
        self.name = "Body"
        self.expressions = expressions

    def build(self, init: Init,  scope: SisalScope):
        """ Build method. Note it's not standard, i.e.
        not using build_method-decorator and has init-node
        as an extra argument"""
        # add ports corresponding to init's new values before
        # the port copied from the parent scope
        self.copy_ports(scope.node)
        self.copy_results_ports(init)
        scope = SisalScope(self)
        self.add_sub_ir(self.expressions.build(self.out_ports, scope))
        del self.expressions
