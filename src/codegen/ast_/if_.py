#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..edge import Edge
from ..cpp.cpp_codegen import CppScope, Variable, indent_cpp, CppBlock


class If(Node):

    def to_cpp(self, scope, block, indent):
        if_scope = CppScope(self.in_ports, scope)
        self.out_ports[0].value = 1

        condition_src = self.condition.to_cpp(if_scope, indent + 1)
        cond_block = CppBlock()

        return f"if({condition_src})\n{1}else{2}"


class Branch(Node):
    pass


class Condition(Node):

    def to_cpp(self, scope, indent):
        cond_scope = CppScope(self.in_ports, scope)

        return f""
