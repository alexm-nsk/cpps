#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator algebraic operations
"""
from ..node import Node  # to_cpp_method
from ..cpp.cpp_codegen import CppVariable, cpp_eval, CppAssignment

OPERATOR_MAP = {
    "=": "==",
    "~=": "!="
}


class Binary(Node):

    def to_cpp(self, block):
        left = cpp_eval(self.in_ports[0], block)
        right = cpp_eval(self.in_ports[1], block)
        result = CppVariable(self.out_ports[0].label
                             if self.out_ports[0].renamed else "bin",
                             self.out_ports[0].type.cpp_type)
        block.add_variable(result)

        # if self.operator == "=":
        #  self.operator = "=="

        for k, v in OPERATOR_MAP.items():
            if self.operator == k:
                self.operator = v

        block.add_code(
            CppAssignment(result, f"{left} {self.operator} {right}")
            )
        self.out_ports[0].value = result


class Unary(Node):

    def to_cpp(self, block):
        operand = cpp_eval(self.in_ports[0], block)

        # result = CppVariable("un", self.out_ports[0].type.cpp_type)

        result = CppVariable(self.out_ports[0].label
                             if self.out_ports[0].renamed else "un",
                             self.out_ports[0].type.cpp_type)

        block.add_variable(result)
        block.add_code(
            CppAssignment(result, f"{self.operator} {operand}")
            )
        self.out_ports[0].value = result
