#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator array access
"""

from ..node import Node
from ..llvm.llvm_codegen import llvm_eval, heap_allocation_helper
import llvmlite.ir as ll
from ..llvm.llvmlite_helpers import i32, i1, i32one, i64, i32zero
from ..error import CodeGenError
from ..type import ArrayType


class ArrayAccess(Node):
    def mark_heap_allocation(self):
        if isinstance(self.out_ports[0].type, ArrayType):
            if self.out_ports[0].type.is_output_array:
                self.in_ports[0].type.is_output_array = True
                heap_allocation_helper(self.in_ports[0])

    def to_llvm(self, irbuilder: ll.IRBuilder):
        # inputs: array, index
        errored_val = llvm_eval(self.in_ports[0], irbuilder)
        array_error_flag = irbuilder.extract_value(errored_val, 0)
        index_errored = llvm_eval(self.in_ports[1], irbuilder)
        label = self.out_ports[0].label if self.out_ports[0].renamed else ""
        # prepare error handling
        error_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_err_block"
        )
        no_error_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_correct_exec_block"
        )
        phi_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_phi_block"
        )
        with irbuilder.goto_block(error_block):
            irbuilder.branch(phi_block)

        # handle error
        index_error = irbuilder.extract_value(index_errored, 0)
        elemer_block = irbuilder.append_basic_block("array_access_out_of_bounds_check")
        validity = irbuilder.or_(index_error, array_error_flag)
        irbuilder.cbranch(
            validity,
            error_block,
            elemer_block,
        )
        # eval errors that depend on index
        irbuilder.position_at_start(elemer_block)
        # array error cond=array of i1s
        index = irbuilder.extract_value(index_errored, 1)
        array_descriptor = irbuilder.extract_value(errored_val, 1)
        bounds = irbuilder.extract_value(array_descriptor, 1)
        # Cloud Sisal Arrays' indices start from 1 by default
        # hence the {index}-1
        if type(index) is not int:
            if index.type == i64:
                index = irbuilder.trunc(index, i32)
            indexIR = irbuilder.sub(index, i32one)
            less_than_zero = irbuilder.icmp_signed("<", indexIR, i32zero)
            more_than_bound = irbuilder.icmp_signed("<", bounds, indexIR)
            out_of_bounds = irbuilder.or_(less_than_zero, more_than_bound)
        else:
            indexIR = i32(index - 1)
            if index - 1 < 0:
                raise CodeGenError(
                    "Literal array index is out of bounds", self.location
                )
        irbuilder.cbranch(
            out_of_bounds,
            error_block,
            no_error_block,
        )
        irbuilder.position_at_start(no_error_block)

        # actual eval logic
        array_ptr = irbuilder.extract_value(array_descriptor, 0)
        res = irbuilder.gep(
            array_ptr,
            [indexIR],
            source_etype=self.in_ports[0].type.element.errored_llvm_type(),
        )
        res = irbuilder.load(
            res,
            name=label,
            typ=self.in_ports[0].type.element.errored_llvm_type(),
        )

        self.out_ports[0].value = res
        # finish error handling
        o_p = self.out_ports[0]
        res_type = o_p.type.errored_llvm_type()
        res_init = res_type(None)
        irbuilder.branch(phi_block)
        with irbuilder.goto_block(error_block):

            error_res = irbuilder.insert_value(res_init, i1(1), 0)
            """ 
            res_inner_type = o_p.type.llvm_type()
            error_res = irbuilder.insert_value(
                res_init, res_inner_type(ll.Undefined), 1
            )"""

        irbuilder.position_at_start(phi_block)

        phi = irbuilder.phi(o_p.type.errored_llvm_type())
        phi.add_incoming(error_res, error_block)
        phi.add_incoming(o_p.value, no_error_block)
        o_p.value = phi
