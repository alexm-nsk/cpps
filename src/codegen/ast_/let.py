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
        # initialization code:
        for i_p, init_i_p in zip(self.in_ports, self.init.in_ports):
            init_i_p.value = i_p.value
        self.init.to_cpp(block, self.body.in_ports)

        self.body.let = self

        for b_i_p, let_i_p in zip(self.body.in_ports[-len(self.in_ports):],
                                  self.in_ports):
            b_i_p.value = let_i_p.value

        # body:
        for o_p, b_o_p in zip(self.out_ports, self.body.out_ports):
            o_p.value = cpp_eval(b_o_p, block)


class LetBody(Node):

    @to_cpp_method
    def to_cpp(self, block: CppBlock):
        # initialization code:
        for i_p, let_i_p in zip(self.in_ports, self.let.in_ports):
            i_p.value = let_i_p.value
