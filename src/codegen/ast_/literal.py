#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator literal
"""
from ..node import Node
from ..cpp.cpp_codegen import CppBlock, cpp_eval  #, CppVariable, CppAssignment


class Literal(Node):

    needs_init = True

    def to_cpp(self, block: CppBlock):
        # if self.value == True:
        #    self.value = "true"

        # literal_variable = CppVariable("literal", self.out_ports[0].type.cpp_type)
        # block.add_variable(literal_variable)
        # block.add_code(CppAssignment(literal_variable, self.value))
        # self.out_ports[0].value = literal_variable

        self.out_ports[0].value = self.value
