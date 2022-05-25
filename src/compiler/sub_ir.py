#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Describes a class that holds nodes and edges
created by 'build' function of nodes
"""

from dataclasses import dataclass
from .node import Node
from .edge import Edge


@dataclass
class SubIr:
    """Contains nodes and edges created by 'build' method of nodes
    A sum ('+') operator can be used with two instances to build one that
    contains nodes and edges from both"""

    nodes: list[Node]
    internal_edges: list[Edge]
    output_edges: list[Edge]

    @property
    def edges(self):
        """returns both internal and output edges"""
        return self.output_edges + self.internal_edges

    def __add__(self, other):
        return SubIr(
            nodes=self.nodes + other.nodes,
            output_edges=self.output_edges + other.output_edges,
            internal_edges=self.internal_edges + other.internal_edges,
        )
