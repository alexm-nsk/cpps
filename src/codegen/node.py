#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node (mostly deserealizing code)
"""
from .port import Port
from .type import get_type
from .edge import Edge


def get_node(node_id):
    return Node.node_index[node_id]


def to_cpp_method(fn):

    def wrapped(self, block):
        if (
            hasattr(self, "name_child_output_values")
            and
            self.name_child_output_values
           ):

            # label the ports:
            for index, o_p in enumerate(self.out_ports):
                src_port = Edge.edge_to[o_p.id].from_
                src_port.label = self.result_name + str(index)

            for o_p in self.out_ports:
                if not o_p.label:
                    if not hasattr(self, "name"):
                        o_p.label = self.name + str(o_p.index)
                    else:
                        o_p.label = self.__class__.__name__ + str(o_p.index)

        return fn(self, block)

    return wrapped


class Node:

    node_index = {}

    @staticmethod
    def get_node(node_id):
        return Node.node_index[node_id]

    @staticmethod
    def parse_port(port):
        return Port(
            Node.get_node(port["node_id"]),
            get_type(port["type"]),  # chooses an appropriate class
            port["index"],
            port["label"] if "label" in port else None,
        )

    def parse_ports(self, in_ports, out_ports):
        if in_ports:
            self.in_ports = [self.parse_port(port) for port in in_ports]
        if out_ports:
            self.out_ports = [self.parse_port(port) for port in out_ports]

    def is_parent(self, compared_node):
        if self == compared_node:
            return True
        if "nodes" not in compared_node.__dict__:
            return False
        if self in compared_node.nodes:
            return True
        return False

    def parse_edges(self, edges):
        self.edges = []
        for edge in edges:
            if "from" in edge and "to" in edge:
                src_index = edge["from"][1]
                dst_index = edge["to"][1]

                src_node = self.node_index[edge["from"][0]]
                dst_node = self.node_index[edge["to"][0]]

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node.__dict__[from_type + "_ports"][src_index]
                to = dst_node.__dict__[to_type + "_ports"][dst_index]

            else:
                # sisal-cl IRs:
                src_index = edge[0]["index"]
                dst_index = edge[1]["index"]

                src_node = self.node_index[edge[0]["node_id"]]
                dst_node = self.node_index[edge[1]["node_id"]]

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node.__dict__[from_type + "_ports"][src_index]
                to = dst_node.__dict__[to_type + "_ports"][dst_index]

            self.edges.append(Edge(from_, to))

    def __init__(self, data):
        Node.node_index[data["id"]] = self
        self.location = data["location"] if "location" in data else None
        self.id = data["id"]
        self.name = data["name"]
        self.parse_ports(
            data["in_ports"] if "in_ports" in data else None,
            data["out_ports"] if "out_ports" in data else None,
        )

        if "nodes" in data:
            self.nodes = [Node.class_map[node["name"]](node)
                          for node in data["nodes"]]

        if "branches" in data:
            self.branches = [Node.class_map["Branch"](br)
                             for br in data["branches"]]

        # sisal-cl IRs only:
        if "results" in data:
            for index, result in enumerate(data["results"]):
                self.out_ports[index].label = result[0]

        # sisal-cl IRs only:
        if "params" in data:
            for index, result in enumerate(data["params"]):
                self.in_ports[index].label = result[0]

        if self.name == "Let":
            from .ast_.let import LetBody

            self.body = LetBody(data["body"])
            del data["body"]

        for field, value in data.items():
            if isinstance(value, dict):
                if "name" in value and value["name"] in self.class_map:
                    self.__dict__[field] = self.class_map[value["name"]](value)
            elif field in ["value", "operator", "function_name", "callee"]:
                self.__dict__[field] = value

        if "edges" in data:
            self.parse_edges(data["edges"])
