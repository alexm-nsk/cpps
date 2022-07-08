#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edges for code generator
"""

from .port import Port


class Edge:

    edges = []
    edges_from = {}
    edge_to = {}

    def __init__(self, from_: Port, to: Port):
        self.from_ = from_
        self.to = to

        if self.from_.id not in Edge.edges_from:
            Edge.edges_from[self.from_.id] = []

        if self.to.id in Edge.edge_to:
            raise Exception(f"There is already an edge pointing at {to}")

        # Edge.edges_to[self.to.id] = []

        Edge.edges_from[self.from_.id].append(self)
        Edge.edge_to[self.to.id] = self
        Edge.edges.append(self)

    def __repr__(self):
        return f"E<{self.from_}, {self.to}>"
