#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""describes sisal scope"""
# pylint: disable=E0602
from __future__ import annotations

from .port import Port
from copy import deepcopy


class SisalScope:
    """base class for scopes"""

    def __init__(self, node):
        self.node = node
        # extra ports for newly defined values
        # like in Init
        self.extra_ports = []

    def add_port(self, port: Port):
        self.extra_ports.append(port)

    def resolve_by_name(self, var_name: str) -> Port:
        """get the port corresponding to this variable in this scope"""
        # pylint: disable=E1101
        # (in_ports may not be present in every node, but are present in ones,
        # which may be scopes)
        for var in self.node.in_ports + self.extra_ports:
            if "label" in var.__dict__:
                if var.label == var_name:
                    return var
        return None

    def get_ports_copy(self, new_node_id: int, start_index: int):
        ports = deepcopy(self.node.ports)
        for index, p in enumerate(ports):
            p.node_id = new_node_id
            p.index = start_index + index
        return ports
