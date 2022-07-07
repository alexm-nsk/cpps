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
        left = cpp_eval(self.in_ports[0], scope, block, indent)
        right = cpp_eval(self.in_ports[1], scope, block, indent)
        # TODO use output port type
        # TODO make addvariable also return it
        result = CppVariable("bin", "int")
        block.add_variable(result)
        block.add_code(CppAssignment(result, f"{left} {self.operator} {right}"))
        self.out_ports[0].value = result


class Unary(Node):
    pass
