#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
describes a class that holds nodes and edges created by 'build' function of nodes
"""

from dataclasses import dataclass
from .node import Node
from .edge import Edge


@dataclass
class SubIr:
    """holds nodes and edges created by 'build' function of nodes"""

    nodes: list[Node]
    internal_edges: list[Edge]
    output_edges: list[Edge]

    """contains returned nodes and edges"""

    @property
    def edges(self):
        """returns both internal and output edges"""
        return self.output_edges + self.internal_edges
