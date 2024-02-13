#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Array initialization node
"""

from ..node import Node, build_method
from ..scope import SisalScope

# from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port
from ..type import ArrayType
from ..error import SisalError


class ArrayInit(Node):

    """Array definition node"""

    def __init__(self, type_definition: Node, items: list[Node],
                 location: str = None):
        super().__init__(location)
        self.name = "ArrayInit"
        self.items = items

        self.in_ports = [
            # the array, type is set later by Edge
            Port(self.id, None, item_index, label=f"item#{item_index}")
            for item_index, item in enumerate(items)
        ]

        self.out_ports = [Port(self.id, None, 0, label="initialized array")]

    def num_out_ports(self) -> int:
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        item_subs = SubIr([], [], [])

        # "sum" doesn't work here because it requires start sum for non int items
        # and adding that would compilcate things

        for (item, port) in zip(self.items, self.in_ports):
            item_subs += item.build([port], scope)

        reference_type = type(self.in_ports[0].type)
        for i_p in self.in_ports[1:]:
            if type(i_p.type) != reference_type:
                raise SisalError("All array items must have the same type.",
                                 location=i_p.type.location)

        # set out port's type using item values' types and
        # location using own location
        self.out_ports[0].type = ArrayType(element=self.in_ports[0].type)
        self.out_ports[0].type.location = self.location

        del self.items
        return SubIr([self], [], []) + item_subs
