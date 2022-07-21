#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator init
"""
from ..node import Node  # to_cpp_method
from ..cpp.cpp_codegen import CppBlock, CppVariable

class Init(Node):

    def to_cpp(self, block: CppBlock):
        for o_p in self.out_ports:
            result = CppVariable(o_p.label, o_p.type)
        self.out_ports[0].value = result
        return "INIT"
