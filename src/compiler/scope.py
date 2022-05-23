#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""describes sisal scope"""
# pylint: disable=E0602
from __future__ import annotations
from dataclasses import dataclass

from .port import Port


@dataclass
class SisalScope:
    """base class for scopes"""
    node: Node

    def resolve_by_name(self, var_name: str) -> Port:
        """get the port corresponding to this variable in this scope"""
        # pylint: disable=E1101
        # (in_ports may not be present in every node, but are present in ones,
        # which may be scopes)
        for var in self.node.in_ports:
            if var.label == var_name:
                return var
        return None
