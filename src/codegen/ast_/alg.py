#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator algebraic operations
"""
from ..node import Node
from ..edge import Edge
from ..cpp.cpp_codegen import CppScope, CppVariable, indent_cpp, CppBlock, cpp_eval, CppAssignment


class Binary(Node):

    def to_cpp(self, scope, block, name="bin"):
        left = cpp_eval(self.in_ports[0], scope, block, "lho")
        right = cpp_eval(self.in_ports[1], scope, block, "rho")
        result = CppVariable(name, self.out_ports[0].type.cpp_type)
        block.add_variable(result)
        block.add_code(CppAssignment(result, f"{left} {self.operator} {right}"))
        self.out_ports[0].value = result


class Unary(Node):
    pass
