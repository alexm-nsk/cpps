#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator algebraic operations
"""
from ..node import Node


class Binary(Node):
    def to_cpp(self, scope, block, indent, name=None):
        pass


class Unary(Node):
    pass
