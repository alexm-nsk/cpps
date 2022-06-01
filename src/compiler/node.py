#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Describes IR-nodes base class
"""
from __future__ import annotations
from itertools import count
from copy import deepcopy
from .edge import Edge
from .sub_ir import SubIr


def build_method(fn):
    def wrapped(self, target_ports: list[Port], scope: SisalScope):
        if len(target_ports) != self.num_out_ports():
            raise Exception(
                f"Error: {len(target_ports)} expressions expected,"
                f"got {len(self.expressions)} at {self.location}"
            )

        out_edges = [
            Edge(out_port, target_port)
            for out_port, target_port in zip(self.out_ports, target_ports)
        ]

        in_edges = (
            [
                Edge(scope_port, in_port)
                for scope_port, in_port in zip(scope.node.in_ports, self.in_ports)
            ]
            if self.connect_parent
            else []
        )

        return fn(target_ports, scope) + SubIr([], in_edges, out_edges)

    return wrapped


class Node:
    """Class for nodes"""

    __ids__ = count()
    # "global" index for all the nodes
    __nodes__ = {}
    no_id = False
    connect_parent = False

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

    def add_sub_ir(self, sub_ir):
        """Add contents of a SubIr to this node's nodes and edges"""
        if sub_ir.nodes:
            if not hasattr(self, "nodes"):
                self.nodes = []
            self.nodes += sub_ir.nodes
        if sub_ir.edges:
            if not hasattr(self, "edges"):
                self.edges = []
            self.edges += sub_ir.edges

    def copy_ports(self, src_node: Node, in_: bool = True, out: bool = True):
        """Copies ports from specified node"""
        if in_:
            self.in_ports = deepcopy(src_node.in_ports)
            for i_p in self.in_ports:
                i_p.node_id = self.id
        if out:
            self.out_ports = deepcopy(src_node.out_ports)
            for o_p in self.out_ports:
                o_p.node_id = self.id

    @classmethod
    def node(cls, id_: str):
        """Returns a node with the specified ID"""
        print(cls.__nodes__[id_])
        return cls.__nodes__[id_]

    @classmethod
    def reset(cls):
        """Resets node indices for recompiling"""
        cls.__nodes__ = {}
        cls.__ids__ = count()

    @classmethod
    def get_id(cls):
        """Returns the id in string form"""
        return "node" + str(next(cls.__ids__))

    def num_out_ports(self):
        """Returns the number of output ports"""
        if hasattr(self, "out_ports"):
            return len(self.out_ports)
        raise Exception(
            f"Number of output ports requested, but node {self.id, type(self)}"
            f" doesn't have out_ports"
        )

    def num_in_ports(self):
        """Returns the number of input ports"""
        if hasattr(self, "in_ports"):
            return len(self.in_ports)
        raise Exception(
            f"Number of input ports requested, but node {self.id}"
            f" doesn't have in_ports"
        )

    def ir_(self, extra_fields: list[str] = []) -> dict:
        """Common for all nodes, converts the fields to export-ready dict
        extra _fields is a list of strings - names of fields special to
        inherited node.
        """
        retval = deepcopy(self.__dict__)
        for key in ["in_ports", "out_ports", "nodes", "edges"]:
            if key in retval:
                retval[key] = [item.ir_() for item in retval[key]]
        for key in extra_fields:
            if key in retval:
                retval[key] = retval[key].ir_()
        return retval

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """supposed to be run before any 'build' in any inherited classes
        as a super().build(target_ports, scope)"""
        if len(target_ports) != self.num_out_ports():
            raise Exception(
                f"Error: {len(target_ports)} expressions expected,"
                f"got {len(self.expressions)} at {self.location}"
            )
