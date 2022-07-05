#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""
from ..node import Node
from ..cpp.cpp_codegen import CppScope, Variable
from ..edge import Edge


class Function(Node):

    functions = {}

    def __init__(self, data):
        super().__init__(data)
        Function.functions[self.function_name] = self

    def to_cpp(self, scope=None):
        ret_type = self.out_ports[0].type

        arg_vars = []
        for port in self.in_ports:
            argument = Variable(port.label, port.type)
            arg_vars += [argument]
            port.value = argument

        # this_function_scope = CppScope(arg_vars)

        arg_str = ", ".join([arg.definition_str() for arg in arg_vars])
        function_string = (
            f"{ret_type.cpp_type} {self.function_name}({arg_str})\n" "{\n" "}"
        )

        for o_p in self.out_ports:
            print(o_p)
            print(Edge.edges_to[o_p.id])

        return function_string
