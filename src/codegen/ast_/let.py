#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator let
"""
from ..node import Node


class Let(Node):
    def to_cpp(self, block):
        self.init.to_cpp(block)


class LetBody(Node):
    pass
