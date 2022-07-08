#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""
from ..node import Node
from ..cpp.cpp_codegen import CppScope, CppBlock, CppVariable, indent_cpp, cpp_eval
from ..edge import Edge


class Function(Node):

    functions = {}

    def __init__(self, data):
        super().__init__(data)
        Function.functions[self.function_name] = self

    def to_cpp(self):
        CppVariable.variable_index = {}
        ret_type = self.out_ports[0].type

        for port in self.in_ports:
            port.value = CppVariable(port.label, port.type)

        this_function_scope = CppScope(self.in_ports)

        arg_str = ", ".join([port.value.definition_str()
                             for port in self.in_ports])

        function_block = CppBlock()

        for o_p in self.out_ports:
            cpp_eval(o_p, this_function_scope, function_block)

        function_string = (
            f"{ret_type.cpp_type} {self.function_name}({arg_str})\n"
            "{\n" +
            indent_cpp(str(function_block)) +
            "\n" +
            indent_cpp(f"return {o_p.value};") +
            "\n}"
        )

        return function_string
