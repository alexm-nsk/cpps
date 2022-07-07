#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..edge import Edge
from ..type import BooleanType
from ..cpp.cpp_codegen import CppScope, CppVariable, indent_cpp, CppBlock


class If(Node):
    def to_cpp(self, scope, block, indent):
        if_scope = CppScope(self.in_ports, scope)
        self.out_ports[0].value = 1

        then_block = CppBlock()
        condition_result = self.condition.to_cpp(if_scope, block, indent + 1)

        block.add_code(f"if({condition_result})\n{then_block}else{2}\n")


class Branch(Node):
    pass


class Condition(Node):
    def to_cpp(self, scope, block, indent):
        cond_scope = CppScope(self.in_ports, scope)
        cond_result = CppVariable("cond", "bool")
        block.add_variable(cond_result)
        return cond_result
