#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loops
"""

from ..node import Node, build_method
from ..port import Port
from ..statement import Statement
from ..scope import SisalScope
from ..sub_ir import SubIr
from .common import Init
from ..type import IntegerType


class LoopBody(Node):
    """Loop body node"""

    def __init__(self, statements: list[Statement], location: str):
        super().__init__(location)
        self.statements = statements


class Cond(Node):
    """Loop condition node, base class"""

    def __init__(self, exp, location: str):
        super().__init__(location)
        self.exp = exp


class PreCond(Cond):
    name = "Pre Condition"


class PostCond(Cond):
    name = "Post Condition"


class Scatter(Node):
    """Iterates over an iterable type"""

    def __init__(self, iteratable):
        super().__init__()
        self.iterable = iteratable
        self.name = "Scatter"

    def num_out_ports(self):
        return 2

    def num_out_ports(self):
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope):
        self.in_ports = [Port(self.id, IntegerType(), 0)]
        self.out_ports = [Port(self.id, None, 0, "element"),
                          Port(self.id, IntegerType(), 1, "index")]
        iterable_ir = self.iterable.build([self.out_ports[0]], scope)
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
        # add port corresponding to this range to parent
        # RangeGen node
        range_gen = range_gen_scope.node
        new_port = Port(range_gen.id, IntegerType(), self.identifier.name)
        range_gen.out_ports.append(new_port)

        return self.scatter_node.build([new_port], range_gen_scope)


class RangeGen(Node):
    """RangeGen node"""

    def __init__(self, ranges: list[Range], location: str):
        super().__init__(location)
        self.ranges = ranges
        self.out_ports = []

        self.name = "RangeGen"

    def build(self, scope):
        self.copy_ports(scope.node, out=False)
        scope = SisalScope(self)
        for n, range_ in enumerate(self.ranges):
            self.add_sub_ir(range_.build(scope))
        del self.ranges


class Loop(Node):
    """Node describing loops"""

    connect_parent = True

    def __init__(self, range_gen, init: Init, body, reduction, location):
        super().__init__(location)
        self.name = "Loop Expression"
        self.init = init
        self.range_gen = range_gen
        self.body = body
        self.reduction = reduction

    def num_in_ports(self):
        pass

    def num_out_ports(self):
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        self.copy_ports(scope.node)
        self.init.build(scope)
        self.range_gen.build(scope)
        del self.body
        del self.reduction
        return SubIr([self], [], [])


class Reduction(Node):
    """Reduction"""

    name = "Reduction"

    def __init__(self, what, of_what, when, location):
        super().__init__(location)
