#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Describes a function call node
"""
from ..node import Node, build_method
from .function import Function
from .multi_exp import MultiExp
from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr
from ..error import SisalError


class Call(Node):
    """Function call node"""

    def __init__(self, name: str, args: MultiExp, location: str):
        super().__init__(location)
        self.callee = name
        self.args = args
        self.name = "FunctionCall"

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        called_function = self.called_function
        self.copy_ports(called_function)

        if self.args:
            for i_p, arg in zip(self.in_ports, self.args.expressions):
                i_p.location = arg.location

            args_ir = self.args.build(self.in_ports, scope)
        else:
            args_ir = SubIr([], [], [])
        del self.args
        if called_function.setup_ports:
            called_function.setup_ports(self)
        return (
            SubIr(
                [self],
                internal_edges=[],
                output_edges=[],
            )
            + args_ir
        )

    @property
    def called_function(self):
        function = Function.get_function(self.callee)
        if not function:
            raise SisalError(
                f'No function named "{self.callee}".',
                self.location,
            )
        return function

    def num_out_ports(self):
        return self.called_function.num_out_ports()

    def num_in_ports(self):
        return self.called_function.num_in_ports()
