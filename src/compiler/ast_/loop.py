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
    """Loop condition node"""

    def __init__(self, exp, location: str):
        super().__init__(location)
        self.exp = exp


class PreCond(Cond):
    name = "Pre Condition"


class PostCond(Cond):
    name = "Post Condition"


class Scatter(Node):
    """Iterates over an iterable type"""

    def __init__(self, iteratable, location: str):
        super().__init__(location)


class RangeNumeric(Node):
    """Numeric range"""

    def __init__(self, left, right, location: str):
        super().__init__(location)


class Range(Node):
    no_id = True
    """(Helper node, deleted in second pass) A single range"""

    def __init__(self, identifier, iterable):
        pass


class RangeGen(Node):
    """RangeGen node"""

    def __init__(self, ranges: list[Range], location: str):
        super().__init__(location)
        self.ranges = ranges
        self.name = "RangeGen"


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
