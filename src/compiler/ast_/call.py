#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
This module describes a function call node
"""
from __future__ import annotations
from ..node import Node
from .function import Function
from .function import MultiExp


class Call(Node):
    """Function call node"""

    def __init__(self, name: str, args: MultiExp, location: str):
        super().__init__(location)

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        pass
