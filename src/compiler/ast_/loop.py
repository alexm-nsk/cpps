#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loops
"""

from ..node import Node, build_method
from ..port import Port
from ..statement import Statement
from ..scope import SisalScope
from ..sub_ir import SubIr
from .multi_exp import MultiExp
from .common import Init, Body


class Loop(Node):
    """Node describing loops"""

    name = "Loop Expression"

    def __init__(self, range, init, body, reduction, location):
        super().__init__(location)

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        pass
