#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator call
"""
from ..node import Node


class FunctionCall(Node):

    def to_cpp(self, scope, indent):
        pass


class BuiltInFunctionCall(Node):
    pass


