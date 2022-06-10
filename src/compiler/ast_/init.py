#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Init node (shared by Loop and Let)
"""

from ..node import Node, build_method
from ..port import Port

from ..scope import SisalScope
from ..sub_ir import SubIr


class Init(Node):

    copy_scope_ports = True
    connect_to_parent = False

    def __init__(self, statements: list, location: str = None):
        super().__init__(location)
        self.name = "Init"
        self.statements = statements

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        pass
