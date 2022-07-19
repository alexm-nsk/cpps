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

        if_results = []

        for index, o_p in enumerate(self.out_ports):
            if_result = CppVariable(name + "_" + str(index + 1),
                                    self.out_ports[index].type.cpp_type)
            if_results.append(if_result)
            block.add_variable(if_result)
            o_p.value = if_result

        condition_result = self.condition.to_cpp(if_scope, block, "if_test")

        then_block = CppBlock()
        else_block = CppBlock()

        for o_p in self.out_ports:
            self.branches[0].to_cpp(o_p, if_scope, then_block)
            self.branches[1].to_cpp(o_p, if_scope, else_block)

        block.add_code(f"if({condition_result})""\n{\n"
                       f"{indent_cpp(str(then_block))}"
                       "\n}\nelse\n"
                       "{\n"
                       f"{indent_cpp(str(else_block))}"
                       "\n}")


class Branch(Node):

    def to_cpp(self, result_port, scope, block, name=None):
        branch_scope = CppScope(self.in_ports, scope)
        self.block = CppBlock()
        block.add_code(
            CppAssignment(
                result_port.value,
                cpp_eval(self.out_ports[result_port.index],
                         branch_scope,
                         block)
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
