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
from .error import SisalError


def build_method(fn):
    def wrapped(self, target_ports: list[Port], scope: SisalScope):
        if len(target_ports) != self.num_out_ports():
            raise SisalError(
                f"Error: {len(target_ports)} "
                f"{'values' if len(target_ports) > 1 else 'value'} expected, "
                f"got {self.num_out_ports()} at ({self.location}) "
                f"node ID: {self.id}, type: {self.name}, target: {target_ports[0].node().name}"
            )

        if self.copy_scope_ports:
            self.copy_ports(scope.node, out=False)
        if self.copy_target_ports:
            self.copy_ports_from_list(target_ports)

        node_sub_ir = fn(self, target_ports, scope)

        out_edges = (
            [
                Edge(out_port, target_port)
                for out_port, target_port in zip(self.out_ports, target_ports)
            ]
            if self.connect_to_parent
            else []
        )
        in_edges = (
            [
                Edge(scope_port, in_port)
                for scope_port, in_port in zip(scope.node.in_ports,
                                               self.in_ports)
            ]
            if self.connect_parent
            else []
        )

        return node_sub_ir + SubIr([], in_edges, out_edges)

    return wrapped


class Node:
    """Class for nodes"""

    # used to keep IDs' count
    __ids__ = count()
    # "global" index for all the nodes
    __nodes__ = {}
    # if True, do not create an ID for this node
    no_id = False
    # connect parent node's input ports to this nodes' input ports
    connect_parent = False
    # connect this node's output ports to parent node's otput ports
    connect_to_parent = True
    # copy ports from the scope this node is contained in
    copy_scope_ports = False
    # copy target ports to output ports when using
    # @build_method decorated method
    copy_target_ports = False

    def __init__(self, location=None):
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
        """Copies ports from the specified node.
        It will replace whatever ports already existed in this node"""
        if in_:
            self.in_ports = deepcopy(src_node.in_ports)
            for i_p in self.in_ports:
                i_p.node_id = self.id
        if out:
            self.out_ports = deepcopy(src_node.out_ports)
            for o_p in self.out_ports:
                o_p.node_id = self.id

    def copy_ports_from_list(self, ports: list[Port]):
        """Copies ports from a list of ports,
        setting correct indices and IDs"""
        self.out_ports = deepcopy(ports)
        for index, port in enumerate(self.out_ports):
            port.index = index
            port.node_id = self.id

    def copy_results_ports(self, src_node: Node):
        """Prepends copies of output ports of src_node
        to this node's in_ports. Used to transfer init's
        results to the body of a Loop or a Let"""
        new_ports = []
        for n_p in deepcopy(src_node.out_ports):
            if n_p.label not in [port.label for port in self.in_ports]:
                n_p.node_id = self.id
                new_ports.append(n_p)

        # prepend new ports to existing ports
        self.in_ports = new_ports + self.in_ports
        # reset port indices
        for index, port in enumerate(self.in_ports):
            port.index = index

    @classmethod
    def node(cls, id_: str):
        """Returns a node with the specified ID"""
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
        raise SisalError(
            f"Number of output ports requested, but node {self.id, type(self)}"
            f" doesn't have out_ports"
        )

    def num_in_ports(self):
        """Returns the number of input ports"""
        if hasattr(self, "in_ports"):
            return len(self.in_ports)
        raise SisalError(
            f"Number of input ports requested, but node {self.id}"
            f" doesn't have in_ports"
        )

    def is_node_parent(self, node):
        """check if this node is contained in specified node's "nodes" """
        if "nodes" not in node.__dict__:
            return False
        return self in node.nodes

    def ir_(self) -> dict:
        """Common for all nodes, converts the fields to export-ready dict"""
        retval = deepcopy(self.__dict__)
        for key in ["in_ports", "out_ports", "nodes", "edges"]:
            if key in retval:
                retval[key] = [item.ir_() for item in retval[key]]
        for key in ["init", "body", "range_gen", "returns", "condition"]:
            if key in retval:
                retval[key] = retval[key].ir_()
        return retval

    def find_sub_node(self, type_: str = None) -> list:
        return [node for node in self.nodes if node.name == type_]

    from .graphml import graphml
    #from .draw_graph import draw_graph
