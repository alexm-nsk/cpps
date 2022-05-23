#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Algebraic operations, bin node and various tools for those
"""

from copy import deepcopy
from ..node import Node
from ..port import Port
from ..scope import SisalScope
from ..sub_ir import SubIr


class Algebraic(Node):
    """Class for algebraic calculations transforms into Bin and operand nodes
    """
    no_id = True

    def __init__(self, expression: list, location: str):
        super().__init__(location)

    def build(self, scope: SisalScope) -> SubIr:
        """Turn algebraic int nodes and edges"""
        scope = SisalScope(self)
        new_nodes = []
        for out_port, out_node in zip(self.out_ports, self.nodes):
            built_data = out_node.build(out_port, scope)
            new_nodes += built_data.nodes
            self.edges += built_data.edges
        self.nodes = new_nodes

    def ir_(self) -> dict:
        """Returns this function as a standard dictionary
        suitable for export"""
        retval = deepcopy(self.__dict__)

        return retval
