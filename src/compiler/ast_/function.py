#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function IR node
"""
from copy import deepcopy
from ..node import Node
from ..port import Port
from ..scope import SisalScope


class Function(Node):
    """Class for functions"""

    def __init__(
        self, function_name: str, args: list, retvals: list, body: list, location: str
    ):
        super().__init__(location)
        self.function_name = function_name
        self.name = "Lambda"

        self.in_ports = [
            Port(self.id, type_, port_index, identifier.name)
            for port_index, [identifier, type_] in enumerate(args)
        ]

        self.out_ports = [
            Port(self.id, type_, port_index) for port_index, type_ in enumerate(retvals)
        ]

        if len(self.out_ports) != len(body):
            raise Exception(
                f"""Function's number of return values doesn't match the """
                f"""number of expected return values: {function_name},
                {location}"""
            )

        self.nodes = body
        self.build()

    def __repr__(self) -> str:
        return str(f"<function ({self.function_name})>")

    def build(self):
        """Recursively rebuilds the function's ir into a dataflow graph"""
        scope = SisalScope(self)
        new_nodes = []
        print(self.nodes)
        for out_port, out_node in zip(self.out_ports, self.nodes):
            built_data = out_node.build(out_port, scope)
            new_nodes += built_data.nodes
            self.edges += built_data.edges
        self.nodes = new_nodes

    def ir_(self) -> dict:
        """Returns this function as a standard dictionary
        suitable for export"""
        retval = super().ir_()

        return retval
