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
from .graphml import GraphMlModule


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
        # <data key="label">A</data>
        if self.label:
            label = '<data key="label"></data>'
            return f'<port name={port_type}{port_index}>label</port>'
        else:
            return f'<port name={port_type}{port_index}/>'
