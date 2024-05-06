#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""

from ..node import Node, to_llvm_method
from ..llvm.llvm_codegen import llvm_eval, BranchCount, heap_allocation_helper
import llvmlite.ir as ll
from ..type import ArrayType
from ..llvm.llvmlite_helpers import i1


class If(Node):

    name = "if"
    copy_parent_input_values = True

    @to_llvm_method
    def to_llvm(self, irbuilder: ll.IRBuilder):

        BranchCount.count += 1  # надо инкапсуляцию

        cond_blocks, errorbr = self.condition.to_llvm(self, irbuilder)
        follower = irbuilder.append_basic_block(name=f"If{BranchCount.count}follower")
        # evaluate branches:
        for o_p in self.out_ports:
            irbuilder.position_at_start(follower)
            errored_type = o_p.type.errored_llvm_type()
            o_p.value = irbuilder.phi(
                errored_type, name=o_p.label if o_p.label else ""
            )  # here arr descriptor very much so
            with irbuilder.goto_block(errorbr):
                errored_val = errored_type(None)
                errored_val = irbuilder.insert_value(errored_val, i1(1), 0)
                o_p.value.add_incoming(errored_val, errorbr)
        for index, then_block in enumerate(cond_blocks):
            then_end_block = irbuilder.append_basic_block(f"{then_block.name}_end")
            irbuilder.position_at_start(then_block)
            for o_p in self.out_ports:
                self.branches[index].to_llvm(self, o_p, irbuilder, then_end_block)
            irbuilder.branch(then_end_block)
            with irbuilder.goto_block(then_end_block):
                irbuilder.branch(follower)
        with irbuilder.goto_block(errorbr):
            irbuilder.branch(follower)
        irbuilder.position_at_end(follower)

    def mark_heap_allocation(self):
        for br in self.branches:
            for o_p, b_o_p in zip(self.out_ports, br.out_ports):
                if isinstance(o_p.type, ArrayType):
                    if o_p.type.is_output_array:
                        b_o_p.type.is_output_array
                        heap_allocation_helper(b_o_p)
            for i_p in self.in_ports:
                b_i_p = next(port for port in br.in_ports if port.label == i_p.label)
                if isinstance(b_i_p.type, ArrayType):
                    if b_i_p.type.is_output_array:
                        i_p.type.is_output_array = True
                        heap_allocation_helper(i_p)


class Branch(Node):

    def to_llvm(self, parent_if, result_port, irbuilder: ll.IRBuilder, endblock):
        for i_p, p_ip in zip(self.in_ports, parent_if.in_ports):
            i_p.value = p_ip.value
        result_port.value.add_incoming(
            llvm_eval(self.out_ports[result_port.index], irbuilder), endblock
        )
        result_port.value._clear_string_cache()


class Condition(Node):
    def to_llvm(self, parent_if, irbuilder: ll.IRBuilder):

        branches = []

        for i_p, p_ip in zip(self.in_ports, parent_if.in_ports):
            i_p.value = p_ip.value
        errorbr = irbuilder.append_basic_block(
            f"If{BranchCount.count}error_in_a_condition"
        )
        for condition_index, o_p in enumerate(self.out_ports):
            cond_result_errored = llvm_eval(o_p, irbuilder)
            cond_error = irbuilder.extract_value(cond_result_errored, 0)
            cond_result = irbuilder.extract_value(cond_result_errored, 1)
            truebr = irbuilder.append_basic_block(
                name=f"If{BranchCount.count}true{condition_index}"
            )
            falsebr = irbuilder.append_basic_block(
                name=f"If{BranchCount.count}false{condition_index}"
            )
            noerrorbr = irbuilder.append_basic_block(
                name=f"If{BranchCount.count}noeror_cond{condition_index}"
            )
            irbuilder.cbranch(cond_error, errorbr, noerrorbr)
            irbuilder.position_at_start(noerrorbr)
            irbuilder.cbranch(cond_result, truebr, falsebr)
            irbuilder.position_at_start(falsebr)
            branches.append(truebr)
        branches.append(irbuilder.block)

        return branches, errorbr
