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
        pragmas: list,
        function_name: str,
        args: list,
        retvals: list,
        body: MultiExp,
        location: str,
    ):
        if self.get_function(function_name):
            raise SisalError(
                message=f'function named "{function_name}" is '
                f"already defined or is a built-in",
                location=location,
            )
        super().__init__(location)
        self.pragmas = pragmas
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

    def analyze(self):
        """find recursions, estimate complexity etc."""
        # print(self.function_name, self.find_sub_node("FunctionCall"))
        pass

    def build(self):
        """Recursively rebuilds the function's ir into a dataflow graph.
        Because it's a top level node it doesn't run the 'super' from Node
        and doesn't take any arguments"""
        scope = SisalScope(self)
        self.add_sub_ir(self.body.build(self.out_ports, scope))
        self.analyze()
        del self.body

    def find_sub_node(self, type_: str) -> list:
        return self.body.find_sub_node(type_)


class BuiltInFunction(Function):
    no_id = True  # not needed but left in in case of future changes

    def __init__(self, function_name: str, args: list, retvals: list, ports_setup=None):
        self.function_name = function_name
        self.name = "Lambda"
        self.is_built_in = True
        self.ports_setup = ports_setup

        self.in_ports = [
            Port(None, type_, port_index, identifier)
            for port_index, [identifier, type_] in enumerate(args)
        ]

        self.out_ports = [
            Port(None, type_, port_index) for port_index, type_ in enumerate(retvals)
        ]

        Function.functions[self.function_name] = self


def array_combine_ports_setup(self):
    pass


Function.built_ins = dict(
    size=BuiltInFunction(
        "size", [["array", ArrayType(element=AnyType())]], [IntegerType()]
    ),
    cos=BuiltInFunction("cos", [["x", RealType()]], [RealType()]),
    addh=BuiltInFunction(
        "addh",
        [["a", ArrayType(element=AnyType())], ["b", AnyType()]],
        [ArrayType(element=AnyType())],
        array_combine_ports_setup,
    ),
    addl=BuiltInFunction(
        "addl",
        [["a", ArrayType(element=AnyType())], ["b", AnyType()]],
        [ArrayType(element=AnyType())],
        array_combine_ports_setup,
    ),
    remh=BuiltInFunction(
        "remh", [["a", ArrayType(element=AnyType())]], [ArrayType(element=AnyType())]
    ),
    reml=BuiltInFunction(
        "reml", [["a", ArrayType(element=AnyType())]], [ArrayType(element=AnyType())]
    ),
)
