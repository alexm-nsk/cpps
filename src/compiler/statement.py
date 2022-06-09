#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Module describing statements
"""

from .node import Node
from .ast_.identifier import Identifier


class Statement:

    pass


class Assignment(Statement):

    def __init__(self, identifier: Identifier, value: Node):
        self.identifier = identifier
        self.value = value
