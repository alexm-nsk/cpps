#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator init
"""
from ..node import Node, to_cpp_method
from ..cpp.cpp_codegen import CppBlock, CppVariable

class Init(Node):

    copy_parent_input_values = True

    @to_cpp_method
    def to_cpp(self, block: CppBlock):
        result = CppVariable("let_result", self.out_ports[0].type)
        self.out_ports[0].value = result
        return "INIT"
