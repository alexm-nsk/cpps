#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Module describing statements
"""

from .node import Node
from .ast_.identifier import Identifier
from .ast_.multi_exp import MultiExp


class Statement:
    pass


class Assignment(Statement):

    def __init__(self, identifier: Identifier, value: Node):
        self.identifier = identifier
        self.value = value


class MultiAssignment(Statement):

    def __init__(self, identifiers: list[Identifier], values: MultiExp):
        self.identifiers = identifiers
        self.values = values
