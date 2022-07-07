#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator algebraic operations
"""
from ..node import Node
from ..edge import Edge
from ..cpp.cpp_codegen import CppScope, CppVariable, indent_cpp, CppBlock, cpp_eval, CppAssignment


class Binary(Node):
    def to_cpp(self, scope, block, indent, name=None):
        print(Edge.edge_to[self.in_ports[0].id].from_)
        print(Edge.edge_to[self.in_ports[0].id].from_.value)
        #left = cpp_eval(self.in_ports[0], scope, block, indent)
        right = cpp_eval(self.in_ports[1], scope, block, indent)

class Unary(Node):
    pass
