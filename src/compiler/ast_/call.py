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


class Call(Node):
    """Function call node"""

    def __init__(self, name: str, args: MultiExp, location: str):
        super().__init__(location)
        self.callee = name
        self.args = args
        self.name = "Call"

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        self.copy_ports(self.called_function())
        args_ir = self.args.build(self.in_ports, scope)
        del self.args
        return (
            SubIr(
                [self],
                internal_edges=[],
                output_edges=[],
            )
            + args_ir
        )

    def called_function(self):
        return Function.functions[self.callee]

    def num_out_ports(self):
        return self.called_function().num_out_ports()

    def num_in_ports(self):
        return self.called_function().num_in_ports()
