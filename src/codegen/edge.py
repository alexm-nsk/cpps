#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edges for code generator
"""

from .port import Port


class Edge:

    edges = []
    edges_from = {}
    edges_to = {}

    def __init__(self, from_: Port, to: Port):
        self.from_ = from_
        self.to = to

        if self.from_.id not in Edge.edges_from:
            Edge.edges_from[self.from_.id] = []

        if self.to.id not in Edge.edges_to:
            Edge.edges_to[self.to.id] = []

        Edge.edges_from[self.from_.id].append(self)
        Edge.edges_to[self.to.id].append(self)
        Edge.edges.append(self)
