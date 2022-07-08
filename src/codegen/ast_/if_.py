#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..cpp.cpp_codegen import (
    CppScope,
    CppVariable,
    indent_cpp,
    CppBlock,
    cpp_eval,
    CppAssignment,
)


class If(Node):
    def to_cpp(self, scope, block, name=None):
        if_scope = CppScope(self.in_ports, scope)
        if_result = CppVariable("if_result", self.out_ports[0].type.cpp_type)
        block.add_variable(if_result)
        self.out_ports[0].value = if_result
        condition_result = self.condition.to_cpp(if_scope, block)
        then_block = CppBlock(add_curly_brackets=True)
        self.branches[0].to_cpp(self, if_scope, then_block)

        block.add_code(f"if({condition_result})\n{str(then_block)}else"
                       "{\n2\n}\n")


class Branch(Node):

    def to_cpp(self, parent_if, scope, block, name=None):
        branch_scope = CppScope(self.in_ports, scope)
        self.block = CppBlock()
        block.add_code(
            CppAssignment(
                parent_if.out_ports[0].value,
                cpp_eval(self.out_ports[0], branch_scope, block)
            )
        )
        #return cond_result


class Condition(Node):
    def to_cpp(self, scope, block, name=None):
        cond_scope = CppScope(self.in_ports, scope)
        cond_result = CppVariable("cond", "bool")
        block.add_variable(cond_result)
        block.add_code(
            CppAssignment(
                cond_result, cpp_eval(self.out_ports[0], cond_scope, block)
            )
        )
        return cond_result
