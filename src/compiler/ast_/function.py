#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function IR node
"""
from ..node import Node
from .multi_exp import MultiExp
from ..port import Port
from ..scope import SisalScope


class Function(Node):
    """Class for function nodes"""

    def __init__(
        self, function_name: str, args: list, retvals: list, body: MultiExp,
        location: str
    ):
        super().__init__(location)
        self.function_name = function_name
        self.name = "Lambda"

        self.in_ports = [
            Port(self.id, type_, port_index, identifier.name)
            for port_index, [identifier, type_] in enumerate(args)
        ]

        self.out_ports = [
            Port(self.id, type_, port_index)
            for port_index, type_ in enumerate(retvals)
        ]

        if len(self.out_ports) != len(body.expressions):
            raise Exception(
                f"""Number of function's return values doesn't match the """
                f"""expected number return values: {function_name},
                {location}"""
            )

        self.body = body
        self.build()

    def __repr__(self) -> str:
        return str(f"<function ({self.function_name})>")

    def build(self):
        """Recursively rebuilds the function's ir into a dataflow graph"""
        scope = SisalScope(self)
        self.add_sub_ir(
                self.body.build(self.in_ports, scope)
            )
        #for out_port, out_node in zip(self.out_ports, self.body.expressions):
            #self.add_sub_ir(out_node.build([out_port], scope))
        del self.body

    def ir_(self) -> dict:
        """Returns this function as a standard dictionary
        suitable for export"""
        retval = super().ir_()

        return retval
