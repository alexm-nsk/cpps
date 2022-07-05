#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port for code generator
"""


from dataclasses import dataclass
from .type import Type
from itertools import count

class Port:

    __ids__ = count()

    def __init__(self, node, type, index, label):
        self.node = node
        self.type = type
        self.index = index
        self.label = label
        self.id = next(Port.__ids__)
        self.value = None

    def get_node(self):
        return Node.get_node(self.node_id)

    def __repr__(self):
        return f"Port<{self.node}, {self.index}, {self.label}, {self.type}, {self.value}>"
