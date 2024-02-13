#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator array access
"""

from ..node import Node
from ..cpp.cpp_codegen import CppBlock, cpp_eval, CppVariable
from ..error import CodeGenError


class ArrayAccess(Node):

    def to_cpp(self, block: CppBlock):
        # inputs: array, index

        array = cpp_eval(self.in_ports[0], block)
        index = cpp_eval(self.in_ports[1], block)

        new_var = CppVariable(self.out_ports[0].label
                              if self.out_ports[0].renamed else "array_access",
                              self.out_ports[0].type.cpp_type)
        block.add_variable(new_var)
        # Cloud Sisal Arrays' indices start from 1 by default
        # hence the {index}-1

        if str(index).isdigit():
            index_string = int(index) - 1
            if index_string < 0:
                raise CodeGenError("Literal array index is out of bounds",
                                   self.location)
        else:
            index_string = f"{index} - 1"

        block.add_code(f"{new_var} = {array}[{index_string}];")
        self.out_ports[0].value = new_var
