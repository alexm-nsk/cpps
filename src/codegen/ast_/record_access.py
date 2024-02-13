#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator array access
"""

from ..node import Node
from ..cpp.cpp_codegen import CppBlock, cpp_eval, CppVariable
from ..error import CodeGenError


class RecordAccess(Node):
    def to_cpp(self, block: CppBlock):
        # inputs: array, index

        record = cpp_eval(self.in_ports[0], block)

        new_var = CppVariable(
            self.out_ports[0].label if self.out_ports[0].renamed else "record_access",
            self.out_ports[0].type.cpp_type,
        )
        block.add_variable(new_var)
        # Cloud Sisal Arrays' indices start from 1 by default
        # hence the {index}-1

        block.add_code(f"{new_var} = {record}.{self.field};")
        self.out_ports[0].value = new_var
