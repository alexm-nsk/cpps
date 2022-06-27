#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function IR node
"""
from ..node import Node
from .multi_exp import MultiExp
from ..port import Port
from ..scope import SisalScope
from ..error import SisalError
from ..type import AnyType, ArrayType, IntegerType, RealType


class Function(Node):
    """Class for function nodes"""

    functions = {}
    built_ins = []  # the list is defined below

    @classmethod
    def reset(cls):
        cls.functions = {}

    @classmethod
    def get_function(cls, name: str):

        if name in Function.functions:
            return Function.functions[name]
        if name in Function.built_ins:
            return Function.built_ins[name]

        return None

    def __init__(
        self,
        function_name: str,
        args: list,
        retvals: list,
        body: MultiExp,
        location: str,
    ):
        if self.get_function(function_name):
            raise SisalError(message=f"function named {function_name} is already defined or is a built-in", location=location)
        super().__init__(location)
        self.function_name = function_name
        self.name = "Lambda"

        self.in_ports = [
            Port(self.id, type_, port_index, identifier.name)
            for port_index, [identifier, type_] in enumerate(args)
        ]

        self.out_ports = [
            Port(self.id, type_, port_index) for port_index, type_ in enumerate(retvals)
        ]

        self.body = body
        Function.functions[self.function_name] = self

    def __repr__(self) -> str:
        return str(f"<function ({self.function_name})>")

    def build(self):
        """Recursively rebuilds the function's ir into a dataflow graph.
        Because it's a top level node it doesn't run the 'super' from Node
        and doesn't take any arguments"""
        if len(self.out_ports) != len(self.body.expressions):
            raise SisalError(
                f"""Number of function's return values doesn't match the """
                f"""expected number return values: {len(self.in_ports)}, """
                f"""name: \"{self.function_name}\".""",
                self.location,
            )
        scope = SisalScope(self)
        self.add_sub_ir(self.body.build(self.out_ports, scope))
        del self.body


class BuiltInFunction(Function):

    no_id = True  # not needed but left in in case of future changes

    def __init__(self, function_name: str, args: list, retvals: list):
        self.function_name = function_name
        self.name = "Lambda"
        self.is_built_in = True

        self.in_ports = [
            Port(None, type_, port_index, identifier)
            for port_index, [identifier, type_] in enumerate(args)
        ]

        self.out_ports = [
            Port(None, type_, port_index)
            for port_index, type_ in enumerate(retvals)
        ]

        Function.functions[self.function_name] = self


Function.built_ins = dict(
    size=BuiltInFunction("size", [["array", ArrayType(element=AnyType())]], [IntegerType()]),
    cos=BuiltInFunction("cos", [["x", RealType]], [RealType]),
)
