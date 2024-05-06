#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator let
"""

from ..node import Node, to_llvm_method
from ..llvm.llvm_codegen import llvm_eval, heap_allocation_helper
import llvmlite.ir as ll
import llvmlite as llvm
from ..type import ArrayType


class Let(Node):

    copy_parent_input_values = True

    @to_llvm_method
    def to_llvm(self, irbuilder: ll.IRBuilder):
        # initialization code:
        for i_p, init_i_p in zip(self.in_ports, self.init.in_ports):
            init_i_p.value = i_p.value
        self.init.to_llvm(irbuilder, self.body.in_ports)

        self.body.let = self

        for b_i_p, let_i_p in zip(
            self.body.in_ports[-len(self.in_ports) :], self.in_ports
        ):
            b_i_p.value = let_i_p.value
        # body:
        for o_p, b_o_p in zip(self.out_ports, self.body.out_ports):
            o_p.value = llvm_eval(b_o_p, irbuilder)

    def mark_heap_allocation(self):
        for o_p, b_o_p in zip(self.out_ports, self.body.out_ports):
            if isinstance(o_p.type, ArrayType):
                if o_p.type.is_output_array:
                    b_o_p.type.is_output_array = True
                    heap_allocation_helper(b_o_p)
        for i_o_p in self.init.out_ports:
            b_i_p = next(
                (
                    port
                    for port in self.body.in_ports
                    if hasattr(port, "label") and port.label == i_o_p.label
                ),
                None,
            )
            if b_i_p:
                if isinstance(b_i_p.type, ArrayType):
                    if b_i_p.type.is_output_array:
                        i_o_p.type.is_output_array = True
                        heap_allocation_helper(i_o_p)
        for b_i_p, i_i_p, let_i_p in zip(
            self.body.in_ports[-len(self.in_ports) :], self.init.in_ports, self.in_ports
        ):
            if isinstance(let_i_p.type, ArrayType):
                let_i_p.type.is_output_array = (
                    b_i_p.type.is_output_array & i_i_p.type.is_output_array
                )
                heap_allocation_helper(let_i_p)


class LetBody(Node):
    @to_llvm_method
    def to_llvm(self, irbuilder: ll.IRBuilder):
        # initialization code:
        for i_p, let_i_p in zip(self.in_ports, self.let.in_ports):
            i_p.value = let_i_p.value
