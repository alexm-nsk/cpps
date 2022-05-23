#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
This module describes node and it's subclasses
"""

from itertools import count

class Node:
    """Class for nodes"""

    __ids__ = count()
    # "global" index for all the nodes
    __nodes__ = {}
    no_id = False

    def __init__(self, location):
        """Not meant to be run on it's own, it adds to child classes'
        initialization"""
        if not self.no_id:
            self.id = self.get_id()
            Node.__nodes__[self.id] = self
        if location is not None:
            self.location = location
        else:
            self.location = "not applicable"
        self.edges = []

    @classmethod
    def node(cls, id_: str):
        """Returns a node with the specified ID"""
        return cls.__nodes__[id_]

    @ classmethod
    def reset(cls):
        """Resets node indices for recompiling"""
        cls.__nodes__ = {}
        cls.__ids__ = count()

    @ classmethod
    def get_id(cls):
        """Returns the id in string form"""
        return "node" + str(next(cls.__ids__))
