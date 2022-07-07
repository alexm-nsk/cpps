#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""
from ..node import Node
from ..cpp.cpp_codegen import CppScope, Variable, indent_cpp
from ..edge import Edge


class Function(Node):

    functions = {}

    def __init__(self, data):
        super().__init__(data)
        Function.functions[self.function_name] = self

    def to_cpp(self, scope=None, indent=0):
        ret_type = self.out_ports[0].type

        for port in self.in_ports:
            port.value = Variable(port.label, port.type)

        this_function_scope = CppScope(self.in_ports)

        arg_str = ", ".join([port.value.definition_str()
                             for port in self.in_ports])

        for o_p in self.out_ports:
            node = Edge.edge_to[o_p.id].from_.node
            function_body = indent_cpp(
                node.to_cpp(this_function_scope, indent + 1)
                )
            o_p.value = Edge.edge_to[o_p.id].from_.value

        function_string = (
            f"{ret_type.cpp_type} {self.function_name}({arg_str})\n"
            "{\n" + str(function_body) + "\n}"
        )

        return function_string
