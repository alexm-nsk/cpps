#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator let
"""
from ..node import Node, to_cpp_method
from ..cpp.cpp_codegen import CppBlock, CppVariable


class Let(Node):

    @to_cpp_method
    def to_cpp(self, block):
        result = CppVariable("let_result", self.out_ports[0].type.cpp_type)
        block.add_variable(result)
        self.out_ports[0].value = result
        self.init.to_cpp(block)


class LetBody(Node):
    pass
