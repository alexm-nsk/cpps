#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Record initialization node
"""

from ..node import Node, build_method
from ..scope import SisalScope

# from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port
from ..type import RecordType
from ..error import SisalError


class RecordInit(Node):

    """Record initialization node"""

    def __init__(self, type_definition: Node, fields: dict[Node],
                 location: str = None):
        super().__init__(location)
        self.name = "RecordInit"
        self.fields = fields

        self.in_ports = [
            # the array, type is set later by Edge
            Port(self.id, None, field_index, label=f"{field}")
            for field_index, (field, value) in enumerate(fields.items())
        ]
        self.port_to_name_index = []
        for port in self.in_ports:
            self.port_to_name_index.append(port.label)

        self.out_ports = [Port(self.id, None, 0, label="initialized record")]

    def num_out_ports(self) -> int:
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        field_subs = SubIr([], [], [])
        field_types = {}
        for ((field, value), port) in zip(self.fields.items(), self.in_ports):
            field_subs += value.build([port], scope)
            field_types[field] = port.type

        self.out_ports[0].type = RecordType(fields=field_types)
        self.out_ports[0].type.location = self.location

        del self.fields
        return SubIr([self], [], []) + field_subs
