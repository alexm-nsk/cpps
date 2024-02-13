#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator init
"""
from ..node import Node  # to_cpp_method
from ..cpp.cpp_codegen import CppBlock, cpp_eval, CppAssignment, CppVariable
from ..edge import get_src_port


class Init(Node):

    # target_ports is tail part of an array of in ports that init variables
    # will be assigned to
    def to_cpp(self, block: CppBlock, target_ports: list = []):

        self.name_child_ports()
        block.add_code("// init:")
        if target_ports:

            for o_p, target_port in zip(self.out_ports, target_ports):
                if o_p.label != target_port.label:
                    raise Exception("(internal) var names in "
                                    "init and body don't match")
                new_variable = cpp_eval(o_p, block)

                o_p.value = new_variable

                if get_src_port(o_p).in_port or (get_src_port(o_p).node.needs_init):
                    o_p.value = CppVariable(o_p.label, o_p.type.cpp_type)
                    block.add_variable(o_p.value)
                    block.add_code(CppAssignment(o_p.value, new_variable))

                target_port.value = o_p.value

        else:

            for o_p in self.out_ports:
                new_variable = cpp_eval(o_p, block)

                if get_src_port(o_p).in_port or (get_src_port(o_p).node.needs_init):
                    o_p.value = CppVariable(o_p.label, o_p.type.cpp_type)
                    block.add_variable(o_p.value)

                    block.add_code(CppAssignment(o_p.value, new_variable))
