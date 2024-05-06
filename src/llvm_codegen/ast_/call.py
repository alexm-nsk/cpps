#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator call
"""

from ..node import Node
from ..edge import Edge
from .function import Function
import llvmlite.ir as ll
from ..llvm.llvm_codegen import llvm_eval
from ..type import ArrayType
from ..llvm.llvmlite_helpers import create_error_handling_blocks, i1


class FunctionCall(Node):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        # check if there is special implementation for this function:
        if self.callee not in FunctionCall.overriden_functions:

            args = [llvm_eval(i_p, irbuilder) for i_p in self.in_ports]

            # timeout = False

            if self.callee in Function.functions:
                called_function = irbuilder.module.get_global(
                    self.callee
                )  # what if callee not translated?

                result = None
                parent_function = self.get_containing_function()

                # if the function has multiple outputs:
                if len(self.out_ports) > 1:
                    name = "call_result"
                    # result = irbuilder.call(called_function, args, name=name)
                    # with errors
                    result = irbuilder.call(called_function, args, name=name)
                    for port_index, o_p in enumerate(self.out_ports):
                        port_result = irbuilder.extract_value(
                            result, port_index, name=f"value_{port_index}"
                        )
                        o_p.value = port_result
                # if the function has one output:
                else:
                    name = (
                        self.out_ports[0].label if self.out_ports[0].renamed else "call"
                    )

                    # result = irbuilder.call(called_function, args, name=name)
                    # with errors
                    result = irbuilder.call(called_function, args, name=name)
                    self.out_ports[0].value = result

        else:
            FunctionCall.overriden_functions[self.callee](self, irbuilder)


"""Overriden implementations (used instead of Function's to_llvm method)"""

from ..llvm.llvmlite_helpers import i32one, i32zero, i64, calc_memsize_at_runtime
from ..type import get_array_descriptor


def remh(self, irbuilder: ll.IRBuilder):
    """Remove first element of an array"""
    name = self.out_ports[0].label if self.out_ports[0].renamed else ""
    src_port = Edge.edge_to[self.in_ports[0].id].from_
    src_type = src_port.type
    errored_arr_descriptor = llvm_eval(self.in_ports[0], irbuilder)
    errcond = irbuilder.extract_value(errored_arr_descriptor, 0)
    err_block, no_err_block, phi_block = create_error_handling_blocks(self, irbuilder)
    irbuilder.cbranch(errcond, err_block, no_err_block)
    with irbuilder.goto_block(phi_block):
        phi = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
    with irbuilder.goto_block(no_err_block):
        array_descriptor = irbuilder.extract_value(errored_arr_descriptor, 1)
        old_ptr = irbuilder.extract_value(array_descriptor, 0)
        old_len = irbuilder.extract_value(array_descriptor, 1)
        new_len = irbuilder.sub(old_len, i32one)
        new_ptr = irbuilder.gep(
            old_ptr, [i32one], source_etype=src_type.element.errored_llvm_type()
        )
        result = irbuilder.insert_value(get_array_descriptor()(None), new_ptr, 0)
        result = irbuilder.insert_value(result, new_len, 1, name=name)
        errored_res = self.out_ports[0].type.pack_val(result, irbuilder)
        phi.add_incoming(errored_res, no_err_block)
        irbuilder.branch(phi_block)
    with irbuilder.goto_block(err_block):
        err = self.out_ports[0].type.make_error(irbuilder)
        phi.add_incoming(err, err_block)
    irbuilder.position_at_start(phi_block)
    self.out_ports[0].value = phi


def reml(self, irbuilder):
    """Remove last element of an array"""
    name = self.out_ports[0].label if self.out_ports[0].renamed else ""
    errored_arr_descriptor = llvm_eval(self.in_ports[0], irbuilder)
    errcond = irbuilder.extract_value(errored_arr_descriptor, 0)
    err_block, no_err_block, phi_block = create_error_handling_blocks(self, irbuilder)
    irbuilder.cbranch(errcond, err_block, no_err_block)
    with irbuilder.goto_block(phi_block):
        phi = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
    with irbuilder.goto_block(no_err_block):
        array_descriptor = irbuilder.extract_value(errored_arr_descriptor, 1)
        old_len = irbuilder.extract_value(array_descriptor, 1)
        new_len = irbuilder.sub(old_len, i32one)
        result = irbuilder.insert_value(self.in_ports[0].value, new_len, 1, name=name)
        errored_res = self.out_ports[0].type.pack_val(result, irbuilder)
        phi.add_incoming(errored_res, no_err_block)
        irbuilder.branch(phi_block)
    with irbuilder.goto_block(err_block):
        err = self.out_ports[0].type.make_error(irbuilder)
        phi.add_incoming(err, err_block)
    irbuilder.position_at_start(phi_block)
    self.out_ports[0].value = phi


def size(self, irbuilder: ll.IRBuilder):
    args = [llvm_eval(i_p, irbuilder) for i_p in self.in_ports]
    errored_arr_descriptor = args[0]
    name = self.out_ports[0].label if self.out_ports[0].renamed else "call"
    errcond = irbuilder.extract_value(errored_arr_descriptor, 0)
    err_block, no_err_block, phi_block = create_error_handling_blocks(self, irbuilder)
    irbuilder.cbranch(errcond, err_block, no_err_block)
    with irbuilder.goto_block(phi_block):
        phi = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
    with irbuilder.goto_block(no_err_block):
        array_descriptor = irbuilder.extract_value(errored_arr_descriptor, 1)
        result = irbuilder.extract_value(array_descriptor, 1)
        # process_timeout()
        result = irbuilder.zext(
            result,
            i64,
            name=name,
        )
        errored_res = self.out_ports[0].type.pack_val(result, irbuilder)
        phi.add_incoming(errored_res, no_err_block)
        irbuilder.branch(phi_block)
    with irbuilder.goto_block(err_block):
        err = self.out_ports[0].type.make_error(irbuilder)
        phi.add_incoming(err, err_block)
    irbuilder.position_at_start(phi_block)
    self.out_ports[0].value = phi


def addh(self, irbuilder: ll.IRBuilder):
    """Add first element to an array"""
    name = self.out_ports[0].label if self.out_ports[0].renamed else ""
    src_port = Edge.edge_to[self.in_ports[0].id].from_
    src_type = src_port.type
    errored_arr_descriptor = llvm_eval(self.in_ports[0], irbuilder)
    errcond = irbuilder.extract_value(errored_arr_descriptor, 0)
    err_block, no_err_block, phi_block = create_error_handling_blocks(self, irbuilder)
    irbuilder.cbranch(errcond, err_block, no_err_block)
    with irbuilder.goto_block(phi_block):
        phi = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
    with irbuilder.goto_block(no_err_block):
        array_descriptor = irbuilder.extract_value(errored_arr_descriptor, 1)
        old_ptr = irbuilder.extract_value(array_descriptor, 0)
        old_len = irbuilder.extract_value(array_descriptor, 1)
        new_len = irbuilder.add(old_len, i32one)
        old_size = calc_memsize_at_runtime(
            irbuilder, src_type.element.llvm_type(), old_len
        )
        new_size = calc_memsize_at_runtime(
            irbuilder, src_type.element.llvm_type(), new_len
        )
        new_ptr = irbuilder.call(irbuilder.module.malloc, [new_size])
        new_head = llvm_eval(self.in_ports[0], irbuilder)
        irbuilder.store(new_head, new_ptr)
        e1_ptr = irbuilder.gep(
            new_ptr, [i32one], source_etype=src_type.element.llvm_type()
        )
        irbuilder.call(irbuilder.module.memcpy, [old_ptr, e1_ptr, old_size, i1(0)])
        result = irbuilder.insert_value(get_array_descriptor()(None), new_ptr, 0)
        result = irbuilder.insert_value(result, new_len, 1, name=name)
        errored_res = self.out_ports[0].type.pack_val(result, irbuilder)
        phi.add_incoming(errored_res, no_err_block)
        irbuilder.branch(phi_block)
    with irbuilder.goto_block(err_block):
        err = self.out_ports[0].type.make_error(irbuilder)
        phi.add_incoming(err, err_block)
    irbuilder.position_at_start(phi_block)
    self.out_ports[0].value = phi


def addl(self, irbuilder: ll.IRBuilder):
    """Add last element to an array"""
    name = self.out_ports[0].label if self.out_ports[0].renamed else ""
    errored_arr_descriptor = llvm_eval(self.in_ports[0], irbuilder)
    errcond = irbuilder.extract_value(errored_arr_descriptor, 0)
    err_block, no_err_block, phi_block = create_error_handling_blocks(self, irbuilder)
    irbuilder.cbranch(errcond, err_block, no_err_block)
    with irbuilder.goto_block(phi_block):
        phi = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
    with irbuilder.goto_block(no_err_block):
        array_descriptor = irbuilder.extract_value(errored_arr_descriptor, 1)
        old_len = irbuilder.extract_value(array_descriptor, 1)
        new_len = irbuilder.zext(irbuilder.add(old_len, i32one), i64)
        old_ptr = irbuilder.extract_value(array_descriptor, 0)
        new_ptr = irbuilder.call(irbuilder.module.realloc, [old_ptr, new_len])
        new_last = llvm_eval(self.in_ports[1], irbuilder)  # TODO err check here
        new_last_ptr = irbuilder.gep(new_ptr, [old_len], source_etype=new_last.type)
        irbuilder.store(new_last, new_last_ptr)
        result = irbuilder.insert_value(get_array_descriptor()(None), new_ptr, 0)
        result = irbuilder.insert_value(result, new_len, 1, name=name)
        errored_res = self.out_ports[0].type.pack_val(result, irbuilder)
        phi.add_incoming(errored_res, no_err_block)
        irbuilder.branch(phi_block)
    with irbuilder.goto_block(err_block):
        err = self.out_ports[0].type.make_error(irbuilder)
        phi.add_incoming(err, err_block)
    irbuilder.position_at_start(phi_block)
    self.out_ports[0].value = phi


FunctionCall.overriden_functions = {
    "remh": remh,
    "reml": reml,
    "size": size,
    "addh": addh,
    "addl": addl,
}

# FunctionCall.built_in_functions = ["size"]


class BuiltInFunctionCall(Node):
    pass
