#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description of IR Edges
"""

from .port import Port
PORT_FULL_DESCRIPTION_IN_EDGES = False


class Edge:

    def __init__(self, from_: Port, to: Port, node):
        self.from_ = from_
        self.to = to
        self.module = node.module
        self.containing_node = node
        node.edges.append(self)
        if self.from_.id not in self.module.edges_from:
            self.module.edges_from[self.from_.id] = []

        if self.to.id in self.module.edge_to:
            raise Exception(f"There is already an edge pointing at {to}")

        # Edge.edges_to[self.to.id] = []

        self.module.edges_from[self.from_.id].append(self)
        self.module.edge_to[self.to.id] = self
        self.module.edges.append(self)

    def attach_origin(self, new_origin):
        if new_origin.id not in self.module.edges_from:
            self.module.edges_from[new_origin.id] = []
        self.module.edges_from[self.from_.id].remove(self)
        self.from_ = new_origin
        self.module.edges_from[new_origin.id].append(self)

    def attach_target(self, new_target):
        self.module.edge_to.pop(self.to.id)
        self.to = new_target
        self.module.edge_to[new_target.id] = self

    def detatch_origin(self):
        self.module.edges_from[self.from_.id].remove(self)
        self.from_ = None

    def detatch_target(self):
        self.module.edge_to[self.to.id] = None
        self.to = None

    def __repr__(self):
        return (f"E<{self.from_.node}:{self.from_.index},"
                f" {self.to.node}:{self.to.index}>")

    def ir_(self):
        """An IR form of this edge as a dict"""
        if PORT_FULL_DESCRIPTION_IN_EDGES:
            return [self.from_.ir_(), self.to.ir_()]
        else:
            return dict(
                from_=(self.from_.node.id, self.from_.index),
                to=(self.to.node.id, self.to.index),
            )


def get_src_node(port: Port):
    return port.node.module.edge_to[port.id].from_.node


def get_src_port(port: Port):
    return port.node.module.edge_to[port.id].from_
