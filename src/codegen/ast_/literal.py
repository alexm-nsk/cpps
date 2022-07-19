#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator literal
"""
from ..node import Node


class Literal(Node):
    def to_cpp(self, block):
        self.out_ports[0].value = self.value
