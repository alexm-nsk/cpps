#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
This module describes an edge
"""
from __future__ import annotations
from dataclasses import dataclass
from .settings import PORT_FULL_DESCRIPTION_IN_EDGES
from .graphml import GraphMlModule


@dataclass
class Edge:
    """Class for edges"""

    from_: Port
    to: Port

    # TODO add type match checks

    # "global" index for all the edges
    __edges__ = []
    __edges_from__ = {}
    __edges_to__ = {}

    @classmethod
    def edge_to_port(cls, port: Port):
        """should be not more than one"""
        for e in cls.__edges__:
            if e.to == port:
                return e

    @classmethod
    def src_port(cls, target_port: Port):
        edge = cls.edge_to_port(target_port)
        return edge.from_

    @classmethod
    def edges_to(cls, node_id: str):
        return cls.__edges_to__[node_id]

    @classmethod
    def edges_from(cls, node_id: str):
        return cls.__from__[node_id]

    @classmethod
    def edges(cls, node_id: str):
        return cls.__edges__[node_id]

    @classmethod
    def reset(cls):
        """Resets edge indices for recompiling"""
        cls.__edges__ = []
        cls.__edges_from__ = {}
        cls.__edges_to__ = {}

    def __post_init__(self):
        """Runs after dataclasses __init__"""
        if self.to.type is None:
            # TODO put it into a log, add a check if its Bin
            self.to.type = self.from_.type
        Edge.__edges__.append(self)
        Edge.__edges_from__[self.from_.node_id] = self
        Edge.__edges_to__[self.to.node_id] = self

    def ir_(self):
        """An IR form of this edge as a dict"""
        if PORT_FULL_DESCRIPTION_IN_EDGES:
            return [
                self.from_.ir_(), self.to.ir_()
                ]
        else:
            return dict(
                from_=(self.from_.node_id, self.from_.index),
                to=(self.to.node_id, self.to.index),
            )

    def gml(self):
        # <edge source="node3" target="node3" sourceport="in0" targetport="out0">
        #     <data key="type">integer</data>
        # </edge>
        src_node = self.from_.node()
        dst_node = self.to.node()

        if src_node.is_node_parent(dst_node):
            dst_port_type = "out"
        else:
            dst_port_type = "in"

        if dst_node.is_node_parent(src_node):
            src_port_type = "in"
        else:
            src_port_type = "out"

        type_str = GraphMlModule.key_str("type", self.to.type.gml())

        gml_str = f'<edge source="{self.from_.node().id}" '\
                  f'target="{self.to.node().id}" '\
                  f'sourceport="{src_port_type}{self.to.index}" '\
                  f'targetport="{dst_port_type}{self.to.index}">\n'\
                  f'{GraphMlModule.indent(type_str)}'\
                  '\n</edge>'
        return gml_str
