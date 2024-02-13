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
from .ast_.multi_exp import MultiExp
from itertools import count


class ParserState:
    warnings = []
    debug_enabled = False
    definitions = {}


def add_definition(name, type_):
    ParserState.definitions[name] = type_


def get_definition(name):
    return ParserState.definitions[name]


def enable_debug():
    ParserState.debug_enabled = True


def disable_debug():
    ParserState.debug_enabled = False


def debug_enabled():
    return ParserState.debug_enabled


def add_warning(text: str):
    ParserState.warnings.append(text)


def get_warnings():
    return ParserState.warnings


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
    ParserState.warnings = []
    ParserState.definitions = {}
    MultiExp.reset()


# TODO move "get_function(name)" here
