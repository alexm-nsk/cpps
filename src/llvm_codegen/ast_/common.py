#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator init
"""

from ..node import Node
from ..llvm.llvm_codegen import llvm_eval
from ..edge import get_src_port
import llvmlite.ir as ll


class Init(Node):

    # target_ports is tail part of an array of in ports that init variables
    # will be assigned to
    def to_llvm(self, irbuilder: ll.IRBuilder, target_ports: list = []):

        self.name_child_ports()
        if target_ports:

            for o_p, target_port in zip(self.out_ports, target_ports):
                if o_p.label != target_port.label:
                    raise Exception(
                        "(internal) var names in " "init and body don't match"
                    )
                new_variable = llvm_eval(o_p, irbuilder)

                o_p.value = new_variable

                """ if get_src_port(o_p).in_port or (get_src_port(o_p).node.needs_init):
                    o_p.value = ll.Constant(o_p.type.llvm_type,new_variable)
                    block.add_variable(o_p.value)
                    block.add_code(CppAssignment(o_p.value, new_variable))"""

                target_port.value = o_p.value

        else:

            for o_p in self.out_ports:
                new_variable = llvm_eval(o_p, irbuilder)
                o_p.value = new_variable

                """if get_src_port(o_p).in_port or (get_src_port(o_p).node.needs_init):
                    o_p.value = CppVariable(o_p.label, o_p.type.cpp_type)
                    block.add_variable(o_p.value)

                    block.add_code(CppAssignment(o_p.value, new_variable))"""
