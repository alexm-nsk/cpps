#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..edge import Edge
from ..cpp.cpp_codegen import CppScope, Variable, indent_cpp


class If(Node):

    def to_cpp(self, scope, indent):
        if_scope = CppScope(self.in_ports, scope)
        print(self.in_ports[0].value)
        self.out_ports[0].value = 1

        cond = 1

        return f"if({cond})\n{1}else{2}"


class Branch(Node):
    pass


class Condition(Node):
    pass
