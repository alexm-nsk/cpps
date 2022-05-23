#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
This module describes node and it's subclasses
"""

from itertools import count
from copy import deepcopy


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

    def ir_(self, extra_fields: list = [str]) -> dict:
        """Common for all nodes, converts the fields to export-ready dict
           extra _fields is a list of strings - names of fields special to
           inherited node.
        """
        retval = deepcopy(self.__dict__)
        for key in ["in_ports", "out_ports", "nodes", "edges"] + extra_fields:
            if key in retval:
                retval[key] = [item.ir_() for item in retval[key]]
        return retval
