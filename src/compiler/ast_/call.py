#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
This module describes a function call node
"""
from __future__ import annotations
from ..node import Node
from .function import Function
from .multi_exp import MultiExp
from ..port import Port
from ..edge import Edge
from ..scope import SisalScope
from ..sub_ir import SubIr


class Call(Node):
    """Function call node"""

    def __init__(self, name: str, args: MultiExp, location: str):
        super().__init__(location)
        self.callee = name
        self.args = args

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        print ("call called")
        pass

    def called_function(self):
        return Function.functions[self.callee]

    def num_out_ports(self):
        return self.called_function().num_out_ports()
