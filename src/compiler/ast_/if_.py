#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
If IR node
"""
from copy import deepcopy
from ..node import Node
from ..port import Port
from ..scope import SisalScope


class If(Node):
    """Class for Ifs"""

    def __init__(
        self,  condition: Node,  then_: list[Node],
        elseifs: list[list[[Node]]],
        else_: list[Node],
        location: str = None
    ):
        super().__init__(location)
        self.condition = condition
        self.then = then_
        self.elseifs = elseifs
        self.else_ = else_
        self.name = "If"

        self.build()

    def __repr__(self) -> str:
        return str(f"<If {self.location})>")

    def build(self, scope: SisalScope):
        """this recursively rebuilds the if's ir into a dataflow graph"""
        scope = deepcopy(SisalScope(self))
        new_nodes = []
        for out_port, out_node in zip(self.out_ports, self.nodes):
            built_data = out_node.build(out_port, scope)
            new_nodes += built_data.nodes
            self.edges += built_data.edges
        self.nodes = new_nodes

    def ir_(self) -> dict:
        """This returns this if as a standard dictionary
        suitable for export"""
        retval = deepcopy(self.__dict__)
        retval["in_ports"] = [i_p.ir_() for i_p in retval["in_ports"]]
        retval["out_ports"] = [o_p.ir_() for o_p in retval["out_ports"]]
        retval["nodes"] = [n__.ir_() for n__ in retval["nodes"]]
        retval["edges"] = [edge.ir_() for edge in retval["edges"]]

        return retval
