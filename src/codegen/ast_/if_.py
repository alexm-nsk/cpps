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
    def to_cpp(self, scope, block, name="if_result"):
        if_scope = CppScope(self.in_ports, scope)
        if_result = CppVariable(name, self.out_ports[0].type.cpp_type)
        block.add_variable(if_result)
        self.out_ports[0].value = if_result
        self.out_ports[1].value = if_result
        condition_result = self.condition.to_cpp(if_scope, block, "if_test")

        then_block = CppBlock()
        else_block = CppBlock()

        self.branches[0].to_cpp(self.out_ports[0].value, 0, if_scope, then_block)
        self.branches[0].to_cpp(self.out_ports[1].value, 1,  if_scope, then_block)
        self.branches[1].to_cpp(self.out_ports[0].value, 0,  if_scope, else_block)

        block.add_code(f"if({condition_result})""\n{\n"
                       f"{indent_cpp(str(then_block))}"
                       "\n}\nelse\n"
                       "{\n"
                       f"{indent_cpp(str(else_block))}"
                       "\n}")


class Branch(Node):

    def to_cpp(self, result_value, port_index, scope, block, name=None):
        branch_scope = CppScope(self.in_ports, scope)
        self.block = CppBlock()
        block.add_code(
            CppAssignment(
                result_value,
                cpp_eval(self.out_ports[port_index], branch_scope, block)
            )
        )


class Condition(Node):
    def to_cpp(self, scope, block, name="cond"):
        cond_scope = CppScope(self.in_ports, scope)
        cond_result = CppVariable(name, "bool")
        block.add_variable(cond_result)
        block.add_code(
            CppAssignment(
                cond_result, cpp_eval(self.out_ports[0], cond_scope, block)
            )
        )
        return cond_result
