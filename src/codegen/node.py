#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node
"""
from .port import Port
from .type import get_type
from .edge import Edge


class Node:

    node_index = {}

    @staticmethod
    def parse_port(port):
        return Port(
            port["node_id"],
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
        if "nodes" not in compared_node.__dict__:
            return False
        if self in compared_node.nodes:
            return True
        return False

    def parse_edges(self, edges):
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

                return Edge(from_, to)
            else:
                raise Exception("sisal-cl compatible JSON irs not implemented")

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
