#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Array access node
"""

from ..node import Node, build_method
from ..scope import SisalScope
from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port


class ArrayAccess(Node):

    def __init__(self, identifier_name, indices: list[Node],
                 location: str = None):
        super().__init__(location)
        self.name = identifier_name

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope):
        self.out_ports = [scope.resolve_by_name(self.name)]
        if self.out_ports == [None]:
            raise SisalError(
                f'identifier "{self.name}" was not defined.', self.location
            )
        return SubIr(nodes=[], output_edges=[], internal_edges=[])
