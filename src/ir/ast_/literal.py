#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator literal
"""
from ..node import Node
from ..type import IntegerType, RealType, BooleanType


class Literal(Node):
    name = "Literal"
    def post_init(self):
        self.value = self.out_ports[0].type.convert(self.value)
