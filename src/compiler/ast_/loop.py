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


class RangeNumeric(Node):
    """Numeric range, iterated over by Scatter"""

    def __init__(self, left, right, location: str):
        super().__init__(location)


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
        range_gen.out_ports.append(
                                    Port(range_gen.id,
                                         None,
                                         self.identifier.name)
                                  )
        return SubIr([], [], [])


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
