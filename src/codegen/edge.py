#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edges for code generator
"""

from dataclasses import dataclass
from .port import Port
from .type import Type


@dataclass
class Edge:

    from_: Port
    to: Port

