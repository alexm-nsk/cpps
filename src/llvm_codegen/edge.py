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

    def attach_origin(self, new_origin):
        if new_origin.id not in Edge.edges_from:
            Edge.edges_from[new_origin.id] = []
        self.from_ = new_origin
        Edge.edges_from[new_origin.id].append(self)

    def attach_target(self, new_target):
        Edge.edge_to.pop(self.to.id)
        self.to = new_target
        Edge.edge_to[new_target.id] = self

    def detatch_origin(self):
        Edge.edges_from[self.from_.id].remove(self)
        self.from_ = None

    def detatch_target(self):
        Edge.edge_to[self.from_.id] = None
        self.to = None

    def __repr__(self):
        return (f"E<{self.from_.node.name}:{self.from_.index},"
                f" {self.to.node.name}:{self.to.index}>")


def get_src_node(port: Port):
    return Edge.edge_to[port.id].from_.node


def get_src_port(port: Port):
    return Edge.edge_to[port.id].from_
