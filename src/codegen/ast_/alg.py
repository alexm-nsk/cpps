#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator algebraic operations
"""
from ..node import Node
from ..cpp.cpp_codegen import CppVariable, cpp_eval, CppAssignment


class Binary(Node):

    def to_cpp(self, block):
        left = cpp_eval(self.in_ports[0], block)
        right = cpp_eval(self.in_ports[1], block)
        result = CppVariable("bin", self.out_ports[0].type.cpp_type)
        block.add_variable(result)
        block.add_code(
            CppAssignment(result, f"{left} {self.operator} {right}")
            )
        self.out_ports[0].value = result


class Unary(Node):

    def to_cpp(self, block):
        name = "un"
        operand = cpp_eval(self.in_ports[0], block)

        result = CppVariable(name, self.out_ports[0].type.cpp_type)
        block.add_variable(result)
        block.add_code(
            CppAssignment(result, f"{self.operator} {operand}")
            )
        self.out_ports[0].value = result
