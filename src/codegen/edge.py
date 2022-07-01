#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edges for code generator
"""

from .port import Port

# from .type import Type


class Edge:

    edges = []
    from_edges = {}
    to_edges = {}

    def __init__(self, from_: Port, to: Port):
        self.from_ = from_
        self.to = to

        if self.from_.node_id not in Edge.from_edges:
            Edge.from_edges[self.from_.node_id] = []

        if self.to.node_id not in Edge.to_edges:
            Edge.to_edges[self.to.node_id] = []

        Edge.from_edges[self.from_.node_id].append(self)
        Edge.to_edges[self.to.node_id].append(self)
        Edge.edges.append(self)
