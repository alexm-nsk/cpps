#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator loop
"""
from ..node import Node
from ..edge import get_src_node
from ..error import CodeGenError


class LoopExpression(Node):
    pass


class Body(Node):
    pass


class Returns(Node):
    pass


class Reduction(Node):
    pass


class RangeGen(Node):
    pass


class RangeNumeric(Node):
    pass


class Scatter(Node):
    pass


class Condition(Node):
    """Not used directly (inherited classes are used instead)"""


class PreCondition(Condition):
    pass


class PostCondition(Condition):
    pass


class OldValue(Node):
    pass
