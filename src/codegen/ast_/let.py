#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator let
"""
from ..node import Node, to_cpp_method
from ..cpp.cpp_codegen import CppBlock, cpp_eval

class Let(Node):

    copy_parent_input_values = True

    @to_cpp_method
    def to_cpp(self, block: CppBlock):

        self.init.to_cpp(block, self.body.in_ports)
        for o_p, b_o_p in zip(self.out_ports, self.body.out_ports):
            o_p.value = cpp_eval(b_o_p, block)


class LetBody(Node):
    pass
