#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
This module describes an edge
"""
from dataclasses import dataclass
from .port import Port


@dataclass
class Edge:
    """Class for edges"""

    from_: Port
    to: Port

    # "global" index for all the edges
    __edges__ = []
    __edges_from__ = {}
    __edges_to__ = {}

    @classmethod
    def reset(cls):
        """Resets edge indices for recompiling"""
        cls.__edges__ = []
        cls.__edges_from__ = {}
        cls.__edges_to__ = {}

    def __post_init__(self):
        """Runs after dataclasses __init__"""
        if self.to.type is None:
            #if type(self.to.node()) != Bin:
                #raise Exception(
                    #"port type should only be defined on the fly for Bin")
            # TODO put it into a log
            self.to.type = self.from_.type
        Edge.__edges__.append(self)
        Edge.__edges_from__[self.from_.node_id] = self
        Edge.__edges_to__[self.to.node_id] = self

    def ir_(self):
        """An IR form of this edge as a dict"""
        return dict(
            from_=(self.from_.node_id, self.from_.index),
            to=(self.to.node_id, self.to.index),
        )
