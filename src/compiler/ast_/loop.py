#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loops
"""

from ..node import Node, build_method
from ..edge import Edge
from ..port import Port
from ..statement import Statement
from ..scope import SisalScope
from ..sub_ir import SubIr
from .common import Init
from ..type import IntegerType, StreamType


class Cond(Node):
    """Loop condition node, base class"""

    def __init__(self, exp, location: str):
        super().__init__(location)
        self.exp = exp
        # copies the name from class, see PreCond/ PostCond
        self.name = self.name

    def build(self, scope: SisalScope):
        del self.exp


class PreCond(Cond):

    name = "Pre Condition"


class PostCond(Cond):

    name = "Post Condition"


class LoopBody(Node):
    """Loop body node, it also forms loop condition object"""

    def __init__(self, statements: list[Statement], location: str):
        super().__init__(location)
        self.name = "Loop Body"
        self.statements = statements
        self.in_ports = []

    def setup_ports(self, scope: SisalScope):
        loop = scope.node
        self.copy_ports(loop, out=False)

        if loop.init:
            self.copy_results_ports(loop.init)

        if loop.range_gen:
            self.copy_results_ports(loop.range_gen)

    def build(self, scope):
        self.setup_ports(scope)
        scope = SisalScope(self)

        self.out_ports = [
            Port(self.id, None, index, exp.identifier.name)
            for index, exp in enumerate(self.statements)
        ]

        for index, definition in enumerate(self.statements):
            self.add_sub_ir(definition.value.build([self.out_ports[index]], scope))
            # here we add newly defined value to the scope
            value_port = Edge.src_port(self.out_ports[index])
            # TODO add option to not change port's label and rather
            # change it in the scope's copy of the port
            value_port.label = definition.identifier.name
            scope.add_port(value_port)

        del self.statements


class Scatter(Node):
    """Iterates over an iterable type"""

    def __init__(self, iterable, location):
        super().__init__(location)
        self.iterable = iterable
        self.name = "Scatter"

    def num_in_ports(self):
        return 1

    def num_out_ports(self):
        return 2

    @build_method
    def build(self, target_ports: list[Port], scope):
        self.in_ports = [Port(self.id, None, 0)]
        iterable_ir = self.iterable.build([self.in_ports[0]], scope)
        element_type = self.in_ports[0].port_type()
        self.out_ports = [
            Port(self.id, StreamType(element=element_type), 0, "element"),
            Port(self.id, IntegerType(), 1, "index"),
        ]
        del self.iterable
        return SubIr([self], [], []) + iterable_ir


class RangeNumeric(Node):
    """Numeric range, iterated over by Scatter"""

    def __init__(self, left, right, location: str):
        super().__init__(location)
        self.name = "Range"
        self.left = left
        self.right = right
        self.out_ports = [Port(self.id, IntegerType(), 0, "range output")]
        self.in_ports = [
            Port(self.id, IntegerType(), 0, "left boundary"),
            Port(self.id, IntegerType(), 1, "right boundary"),
        ]

    @build_method
    def build(self, target_ports: list[Port], scope):
        left_ir = self.left.build([self.in_ports[0]], scope)
        right_ir = self.right.build([self.in_ports[1]], scope)
        del self.left
        del self.right
        return SubIr([self], [], []) + left_ir + right_ir


class Range(Node):
    """(Helper node, deleted in second pass) A single range"""

    no_id = True

    def __init__(self, identifier, scatter_node):
        self.identifier = identifier
        self.scatter_node = scatter_node

    def build(self, range_gen_scope: SisalScope) -> SubIr:
        # add ports corresponding to this range to parent
        # RangeGen node
        range_gen = range_gen_scope.node
        index = len(range_gen.out_ports)
        new_value_port = Port(range_gen.id, None, index, label=self.identifier.name)
        new_index_port = Port(
            range_gen.id,
            IntegerType(),
            index + 1,
            label=self.identifier.name + "_index",
        )
        range_gen.out_ports += [new_value_port, new_index_port]

        return self.scatter_node.build(range_gen.out_ports, range_gen_scope)


class RangeGen(Node):
    """RangeGen node"""

    def __init__(self, ranges: list[Range], location: str):
        super().__init__(location)
        self.ranges = ranges
        self.name = "RangeGen"
        self.out_ports = []

    def build(self, scope):
        self.copy_ports(scope.node, out=False)
        scope = SisalScope(self)
        for n, range_ in enumerate(self.ranges):
            self.add_sub_ir(range_.build(scope))
        del self.ranges


class Reduction(Node):
    """Reduction segment"""

    no_id = True

    def __init__(self, what, of_what, when, location):
        super().__init__(location)
        self.what = what
        self.of_what = of_what
        self.when = when

    def build(self, scope):
        loop = scope.node
        self.copy_ports(scope.node, out=False)
        if "init" in loop.__dict__:
            self.copy_results_ports(loop.init)
        if "range_gen" in loop.__dict__:
            self.copy_results_ports(loop.range_gen)
        scope = SisalScope(self)

        self.operator = self.what
        # self.of_what.build(scope)

        del self.what
        del self.of_what
        del self.when


class Returns(Node):
    """Returns (or Ret as it's called in Sisal 3.1)"""

    def __init__(self, reduction_segments: list[Reduction], location):
        super().__init__(location)
        self.name = "Reduction"
        self.reduction_segments = reduction_segments

    def build(self, scope):
        del self.reduction_segments
        pass


class Loop(Node):
    """Node describing loops"""

    connect_parent = True

    def __init__(self, range_gen, init: Init, body, condition, reduction, location):
        super().__init__(location)
        self.init = init
        self.name = "Loop Expression"
        self.range_gen = range_gen
        self.body = body
        self.condition = condition
        self.reduction = reduction

    def num_out_ports(self):
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        self.copy_ports(scope.node)
        scope = SisalScope(self)
        for item in ["init", "range_gen", "body", "condition", "reduction"]:
            if self.__dict__[item]:
                self.__dict__[item].build(scope)
            else:
                del self.__dict__[item]

        return SubIr([self], [], [])
