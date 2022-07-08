#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator call
"""
from ..node import Node
from ..cpp.cpp_codegen import (
    CppScope,
    CppVariable,
    indent_cpp,
    CppBlock,
    cpp_eval,
    CppAssignment,
)


class FunctionCall(Node):

    def to_cpp(self, scope, block, name=None):
        left = cpp_eval(self.in_ports[0], scope, block)
        result = CppVariable("call", self.out_ports[0].type.cpp_type)
        block.add_variable(result)
        args = ""
        block.add_code(CppAssignment(result, f"{self.callee} {args}"))
        self.out_ports[0].value = result


class BuiltInFunctionCall(Node):
    pass
