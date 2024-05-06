#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator record initialization
"""

from ..node import Node
from ..llvm.llvm_codegen import llvm_eval
import llvmlite.ir as ll
from ..error import CodeGenError


class RecordInit(Node):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        # inputs: array, index

        items = [llvm_eval(i_p, irbuilder) for i_p in self.in_ports]
        types = [ll.IntType(len(items))] + [item.type for item in items]

        record_type = ll.LiteralStructType(types)

        new_var = record_type(None)

        for port_index, value in enumerate(items):
            irbuilder.insert_value(new_var, value, port_index + 1)

        self.out_ports[0].value = self.out_ports[0].type.pack_val(new_var, irbuilder)
