#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..cpp.cpp_codegen import (
    CppVariable,
    indent_cpp,
    CppBlock,
    cpp_eval,
    CppAssignment,
)


class If(Node):
    def to_cpp(self, block):
        name = "if_result"

        for o_p in self.out_ports:
            if not o_p.label:
                o_p.label = name + str(o_p.index)

        for i_p in self.in_ports:
            cpp_eval(i_p, block)

        if_results = []

        for index, o_p in enumerate(self.out_ports):
            if_result = CppVariable(o_p.label,
                                    self.out_ports[index].type.cpp_type)
            if_results.append(if_result)
            block.add_variable(if_result)
            o_p.value = if_result

        condition_result = self.condition.to_cpp(self, block)

        then_block = CppBlock()
        else_block = CppBlock()

        for o_p in self.out_ports:
            self.branches[0].to_cpp(self, o_p, then_block)
            self.branches[1].to_cpp(self, o_p, else_block)

        block.add_code(f"if({condition_result})""\n{\n"
                       f"{indent_cpp(str(then_block))}"
                       "\n}\nelse\n"
                       "{\n"
                       f"{indent_cpp(str(else_block))}"
                       "\n}")


class Branch(Node):

    def to_cpp(self, parent_if, result_port, block):
        for i_p, p_ip in zip(self.in_ports, parent_if.in_ports):
            i_p.value = p_ip.value
        self.block = CppBlock()
        block.add_code(
            CppAssignment(
                result_port.value,
                cpp_eval(self.out_ports[result_port.index],
                         block)
            )
        )


class Condition(Node):
    def to_cpp(self, parent_if, block):
        name = "if_test"
        for i_p, p_ip in zip(self.in_ports, parent_if.in_ports):
            i_p.value = p_ip.value
        cond_result = CppVariable(name, "bool")
        block.add_variable(cond_result)
        block.add_code(
            CppAssignment(
                cond_result, cpp_eval(self.out_ports[0], block)
            )
        )
        return cond_result
