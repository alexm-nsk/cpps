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
from .multi_exp import MultiExp
from .common import Init, Body


class LoopBody(Node):
    """Loop body node"""

    def __init__(self, statements, location: str):
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
    """Scatter node"""

    def __init__(self, identifier, iteratable, location: str):
        super().__init__(location)


class RangeNumeric(Node):
    """Scatter node"""

    def __init__(self, identifier, left, right, location: str):
        super().__init__(location)


class RangeGen(Node):
    """RangeGen node"""

    def __init__(self, ranges, location: str):
        super().__init__(location)
        self.ranges = ranges


class Loop(Node):
    """Node describing loops"""

    connect_parent = True

    def __init__(self, ranges, init: Init, body, reduction, location):
        super().__init__(location)
        self.name = "Loop Expression"
        self.init = init
        self.ranges = ranges
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
        del self.body
        del self.reduction
        del self.ranges
        return SubIr([self], [], [])


class Reduction(Node):
    """Reduction"""

    name = "Reduction"

    def __init__(self, what, of_what, when, location):
        super().__init__(location)
