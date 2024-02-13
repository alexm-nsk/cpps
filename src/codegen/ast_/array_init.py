#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator array initialization
"""

from ..node import Node
from ..cpp.cpp_codegen import CppBlock, cpp_eval, CppVariable
from ..error import CodeGenError


class ArrayInit(Node):

    def to_cpp(self, block: CppBlock):
        # inputs: array, index

        items = [str(cpp_eval(i_p, block)) for i_p in self.in_ports]

        new_var = CppVariable(self.out_ports[0].label
                              if self.out_ports[0].renamed else "array_init",
                              self.out_ports[0].type.cpp_type)

        block.add_variable(new_var)

        block.add_code(f"{new_var} = "  "{" f"{', '.join(items)}" "}" ";")
        self.out_ports[0].value = new_var
