#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edges for code generator
"""

from dataclasses import dataclass
from .port import Port
# from .type import Type


edges = []
from_edges = {}
to_edges = {}


@dataclass
class Edge:

    from_: Port
    to: Port

    def __post_init__(self):
        if self.from_.node_id not in from_edges:
            from_edges[self.from_.node_id] = []

        if self.to.node_id not in to_edges:
            to_edges[self.to.node_id] = []

        from_edges[self.from_.node_id].append(self)
        to_edges[self.to.node_id].append(self)
        edges.append(self)
