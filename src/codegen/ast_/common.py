#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator init
"""
from ..node import Node  # to_cpp_method
from ..cpp.cpp_codegen import CppBlock, cpp_eval, CppVariable


class Init(Node):

    # target_ports is tail part of an array of in ports that init variables
    # will be assigned to
    def to_cpp(self, block: CppBlock, target_ports):

        self.name_child_ports()

        for o_p, target_port in zip(self.out_ports, target_ports):
            if o_p.label != target_port.label:
                raise Exception("(internal) var names in "
                                "init and body don't match")
            new_variable = cpp_eval(o_p, block)

            o_p.value = new_variable
            target_port.value = new_variable
