#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IR Port
"""

from .type import Type
from itertools import count
from copy import deepcopy

DONT_ADD_EMPTY_LABELS = True


class Port:
    __ids__ = count()

    def __init__(
        self, node, type: Type, index, label, in_port: bool, location: str = None
    ):
        self.node = node
        self.type = type
        self.index = index
        self.label = label
        self.id = next(Port.__ids__)
        self.in_port = in_port  # shows if is it an in-port
        if location:
            self.location = location
        # TODO detect in_port by checking if it is in in_ports
        # of node indtead of passing as a parameter

    @property
    def connected_ports(self) -> list:
        return [edge.to for edge in self.node.module.edges_from[self.id]]

    @property
    def input_port(self):
        return self.node.module.edge_to[self.id].from_

    @property
    def input_node(self):
        """Returns the node connected to this port via one edge"""
        return self.node.module.edge_to[self.id].from_.node

    @property
    def target_nodes(self) -> list:
        """Returns the list of nodes this port is connected to"""
        return [edge.to.node for edge in self.node.module.edges_from[self.id]]

    def __repr__(self):
        return f"Port<{self.node}, {self.index}, {self.label}" f", {self.type}>"

    def ir_(self):
        """Exports port's IR form as a dict"""
        retval = deepcopy(self.__dict__)
        retval["node_id"] = retval["node"].id
        del retval["node"]
        del retval["id"]
        del retval["in_port"]
        if self.label is None and DONT_ADD_EMPTY_LABELS:
            del retval["label"]
        retval.update(type=self.type.ir_())
        return retval

    @property
    def output_edges(self):
        '''Returns all edges beginning from this port'''
        if self.id in self.node.module.edges_from:
            return self.node.module.edges_from[self.id]
        else:
            return []

    @property
    def input_edge(self):
        '''Returns an edge pointing to this port (or None if there isn't one)'''
        if self.id in self.node.module.edge_to:
            return self.node.module.edge_to[self.id]
        else:
            return None

def copy_port_labels(src_ports, dst_ports):
    for src, dst in zip(src_ports, dst_ports):
        dst.label = src.label
