#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator call
"""
from ..node import Node
from ..edge import Edge
from .function import Function, time_limited_execution_cpp

from ..cpp.cpp_codegen import (
    CppVariable,
    CppBlock,
    cpp_eval,
    CppAssignment,
)


class FunctionCall(Node):

    def to_cpp(self, block: CppBlock):
        # check if there is special implementation for this function:
        if self.callee not in FunctionCall.overriden_functions:
            # build function arguments string
            arg_vars = [str(cpp_eval(i_p, block)) for i_p in self.in_ports]
            args = ", ".join(arg_vars)

            timeout = False
            # check if it isn't a built in function:
            if self.callee in Function.functions:
                called_function = Function.functions[self.callee]
                timeout_pragma = called_function.get_pragma("max_time")
                if timeout_pragma:
                    result_name, exec_code = time_limited_execution_cpp(
                                             Function.functions[self.callee],
                                             args)
                    block.add_code(exec_code)
                    timeout = True

            result = None

            def process_timeout():
                if timeout:
                    block.add_code(CppAssignment(result,
                                   f"{result_name}.retval"))
                else:
                    block.add_code(CppAssignment(result,
                                   f"{self.callee}({args})"))

            # if the function has multiple outputs:
            if len(self.out_ports) > 1:
                name = "call_result"
                called_function = Function.functions[self.callee]
                result = CppVariable(name, called_function.ret_cpp_type)
                process_timeout()
                block.add_variable(result)
                for port_index, o_p in enumerate(self.out_ports):
                    type_ = called_function.out_ports[port_index].type.cpp_type
                    port_result = CppVariable(f"value_{port_index}", type_)
                    block.add_variable(port_result)
                    block.add_code(CppAssignment(
                                   port_result,
                                   f"get<{port_index}>({result.name})"))
                    o_p.value = port_result
            # if the function has one output:
            else:
                name = (self.out_ports[0].label
                        if self.out_ports[0].renamed else "call")
                result_type = self.out_ports[0].type
                result = CppVariable(name, result_type.cpp_type)
                block.add_variable(result)
                process_timeout()
                self.out_ports[0].value = result
        else:
            FunctionCall.overriden_functions[self.callee](self, block)


'''Overriden implementations (used instead of Function's to_cpp method)'''


def remh(self, block: CppBlock):
    '''Remove first element of an array'''
    name = (self.out_ports[0].label
            if self.out_ports[0].renamed else "remh_call")
    src_port = Edge.edge_to[self.in_ports[0].id].from_
    result_type = src_port.type
    result = CppVariable(name, result_type.cpp_type)
    block.add_variable(result)
    arg_vars = [str(cpp_eval(i_p, block)) for i_p in self.in_ports]
    args = ", ".join(arg_vars)
    block.add_code(CppAssignment(result, f"{self.callee}({args})"))
    self.out_ports[0].value = result


def reml(self, block: CppBlock):
    '''Remove last element of an array'''
    name = (self.out_ports[0].label
            if self.out_ports[0].renamed else "reml_call")
    src_port = Edge.edge_to[self.in_ports[0].id].from_
    result_type = src_port.type
    result = CppVariable(name, result_type.cpp_type)
    block.add_variable(result)
    arg_vars = [str(cpp_eval(i_p, block)) for i_p in self.in_ports]
    args = ", ".join(arg_vars)
    block.add_code(CppAssignment(result, f"{self.callee}({args})"))
    self.out_ports[0].value = result


FunctionCall.overriden_functions = {
    "remh": remh,
    "reml": reml,
}

FunctionCall.built_in_functions = [
    "size"
]


class BuiltInFunctionCall(Node):
    pass
