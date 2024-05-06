#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator array initialization
"""

import math
import llvmlite.ir as ll
import llvmlite.binding as llvm
from ..type import ArrayType, get_array_descriptor

# import llvmlite.binding as llvm
from ..node import Node
from ..llvm.llvm_codegen import llvm_eval, heap_allocation_helper
from ..llvm.llvmlite_helpers import calc_memsize_at_runtime, i32, i64, i1

# from ..error import CodeGenError


class ArrayInit(Node):

    def mark_heap_allocation(self):
        type_ = self.out_ports[0].type
        output_array = type_.is_output_array
        dim = type_.dimensions()
        if output_array and dim > 1:
            for i_p in self.in_ports:
                i_p.type.is_output_array = True
                heap_allocation_helper(i_p)

    def to_llvm(self, irbuilder: ll.IRBuilder):
        # inputs: array, index
        type_ = self.out_ports[0].type
        items = [llvm_eval(i_p, irbuilder) for i_p in self.in_ports]
        type_.count = len(items)
        etyp = type_.element.errored_llvm_type()
        arg = calc_memsize_at_runtime(
            irbuilder, etyp, type_.count
        )  # here either elemtype+count or get raw
        ptr = irbuilder.call(
            irbuilder.module.malloc,
            [arg],
        )
        parent_function = self.get_containing_function()
        parent_function.mallocs.add(ptr)
        if self.out_ports[0].type.is_output_array:
            parent_function.preserved_mallocs.add(ptr)

        for index, i_p in enumerate(self.in_ports):
            indexIR = i32(index)
            target = irbuilder.gep(
                ptr,
                [indexIR],
                source_etype=etyp,
            )
            int_ = irbuilder.ptrtoint(target, i64)
            target = irbuilder.inttoptr(int_, ll.PointerType())
            irbuilder.store(i_p.value, target)
        record_type = type_.llvm_type()
        new_var = ll.Constant(record_type, None)
        new_var = irbuilder.insert_value(new_var, ptr, 0)
        new_var = irbuilder.insert_value(new_var, i32(type_.count), 1)
        errored_ret_type = type_.errored_llvm_type()
        errored_ret_val = errored_ret_type(None)
        errored_ret_val = irbuilder.insert_value(errored_ret_val, i1(0), 0)
        errored_ret_val = irbuilder.insert_value(errored_ret_val, new_var, 1)
        self.out_ports[0].value = errored_ret_val
