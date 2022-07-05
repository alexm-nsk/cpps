#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..edge import Edge


class If(Node):

    def to_cpp(self, scope, indent):
        self.out_ports[0].value = 1

        cond = 1

        return f"if({cond})\n{1}else{2}"


class Branch(Node):
    pass


class Condition(Node):
    pass
