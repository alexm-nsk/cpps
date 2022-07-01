#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port for code generator
"""


from dataclasses import dataclass
from .type import Type


@dataclass
class Port:
    node_id: int
    type: Type
    index: int
    label: str
