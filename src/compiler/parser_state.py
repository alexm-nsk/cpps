#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Parser's state - provides access to all nodes, edges functions and definitions.
Also provides a method to reset the whole state.
"""

from .node import Node
from .edge import Edge
from .ast_.function import Function


def node(node_id: str):
    return Node.node(node_id)


def edges_to(node_id: str):
    return Edge.edges_to(node_id)


def edges_from(node_id: str):
    return Edge.edges_from(node_id)


def reset():
    """Reset parser's state.
    Clears Node, Edge, Function indices.
    Resets the node ids.
    """
    Edge.reset()
    Node.reset()
    Function.reset()
