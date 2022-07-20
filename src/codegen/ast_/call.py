#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator call
"""
from ..node import Node
from ..cpp.cpp_codegen import (
    CppVariable,
    CppBlock,
    cpp_eval,
    CppAssignment,
)


class FunctionCall(Node):
    def to_cpp(self, block):
        name = "call"
        result = CppVariable(name, self.out_ports[0].type.cpp_type)
        block.add_variable(result)

        arg_vars = [str(cpp_eval(i_p, block)) for i_p in self.in_ports]
        args = ", ".join(arg_vars)

        block.add_code(CppAssignment(result, f"{self.callee}({args})"))
        self.out_ports[0].value = result


class BuiltInFunctionCall(Node):
    pass
