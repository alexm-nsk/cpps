#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Describes sisal ports"""
# pylint: disable=E0602
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from .type import Type
from .settings import DONT_ADD_EMPTY_LABELS
from .node import Node
from .graphml import GraphMlModule as gml


@dataclass
class Port:
    """Describes a sisal port"""

    node_id: str
    type: Type
    index: int
    label: str = None

    def node(self):
        """Get the node this port belongs to"""
        return Node.node(self.node_id)

    def port_type(self):
        return self.type

    def ir_(self):
        """Exports port's IR form as a dict"""
        retval = deepcopy(self.__dict__)
        if self.label is None and DONT_ADD_EMPTY_LABELS:
            del retval["label"]
        retval.update(type=self.type.ir_())
        return retval

    def graphml(self, port_type):
        port_index = self.index
        type_str = f'type="{self.type.gml()}"'
        header = f'<port name="{port_type}{port_index}" {type_str}'
        if self.label:
            label = gml.key_str("label", self.label)
            return header + ">\n" + f"{gml.indent(label,1)}\n</port>"
        else:
            return header + "/>"

    def input_chain_height():
        '''calculates the longest chain leading to this port'''
        pass
