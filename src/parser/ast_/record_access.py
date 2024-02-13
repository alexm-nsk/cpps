#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Rercord access node
"""

from ..node import Node, build_method
from ..scope import SisalScope

# from ..error import SisalError
from ..sub_ir import SubIr
from ..port import Port

from ..error import SisalError


class RecordAccess(Node):

    """Record access node"""

    def __init__(self, record: Node, field: str, location: str = None):
        super().__init__(location)
        self.name = "RecordAccess"

        self.record = record
        self.field = field

        # get type from input and get type from that record's description
        self.in_ports = [
            Port(self.id, None, 0, label="record")
        ]

        self.out_ports = [Port(self.id, None, 0)]

    def num_out_ports(self) -> int:
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """RecordAccess's build method"""

        record_ir = self.record.build([self.in_ports[0]], scope)

        self.out_ports[0].type = self.in_ports[0].type.fields[self.field]

        del self.record

        return (
            SubIr([self], [], []) + record_ir
        )
