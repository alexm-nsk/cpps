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

    def __init__(self, node_id, type, index, label):
        self.node_id = node_id
        self.type = type
        self.index = index
        self.label = label
        self.id = next(Port.__ids__)
