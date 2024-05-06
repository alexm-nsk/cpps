#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator literal
"""

from ..node import Node
import llvmlite.ir as ll
import llvmlite as llvm
from ..llvm.llvmlite_helpers import i1


class Literal(Node):

    needs_init = True

    def to_llvm(self, irbuilder: ll.IRBuilder):
        val = ll.Constant(self.out_ports[0].type.llvm_type(), self.value)
        self.value = val
        errored_type = self.out_ports[0].type.errored_llvm_type()
        errored_val = errored_type(None)
        errored_val = irbuilder.insert_value(errored_val, val, 1)
        errored_val = irbuilder.insert_value(errored_val, i1(0), 0)
        self.out_ports[0].value = errored_val
