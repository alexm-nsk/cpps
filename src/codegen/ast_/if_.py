#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..cpp.cpp_codegen import CppScope, CppVariable, indent_cpp, CppBlock, cpp_eval, CppAssignment


class If(Node):
    def to_cpp(self, scope, block, indent, name=None):
        if_scope = CppScope(self.in_ports, scope)

        then_block = CppBlock(add_curly_brackets=True)
        condition_result = self.condition.to_cpp(if_scope, block, indent + 1)

        block.add_code(
            f"if({condition_result})\n{str(then_block)}else"
            "{\n2\n}\n"
        )


class Branch(Node):
    pass


class Condition(Node):
    def to_cpp(self, scope, block, indent, name=None):
        cond_scope = CppScope(self.in_ports, scope)
        cond_result = CppVariable("cond", "bool")
        block.add_variable(cond_result)
        block.add_code(
                    CppAssignment(
                        cond_result,
                        cpp_eval(self.out_ports[0], cond_scope, block, 1)
                    )
                )
        return cond_result
