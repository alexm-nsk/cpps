#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node
"""
from .port import Port
from .type import Type
from .edge import Edge


class Node:

    nodes = {}

    @staticmethod
    def parse_port(port):
        return Port(
            port["node_id"],
            Type(port["type"]),
            port["index"],
            port["label"] if "label" in port else None,
        )

    def parse_ports(self, in_ports, out_ports):
        if in_ports:
            self.in_ports = [self.parse_port(port) for port in in_ports]
        if out_ports:
            self.out_ports = [self.parse_port(port) for port in out_ports]

    def is_parent(self, compared_node: Node):
        if "nodes" not in compared_node:
            return False
        if self in compared_node["nodes"]:
            return True
        return False

    def parse_edges(self, edges):
        for edge in edges:
            if "from" in edge and "to" in edge:
                src_index = edge["from"][1]
                dst_index = edge["to"][1]

                src_node = Node.nodes[edge["from"][0]]
                dst_node = Node.nodes[edge["to"][0]]

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node[from_type + "_ports"][src_index]
                to = dst_node[to_type + "_ports"][dst_index]

                return Edge(from_, to)
            else:
                pass

            self.edges.append(
                            Edge(from_, to)
                            )

    def __init__(self, data):
        self.name = data["name"]
        self.parse_ports(data["in_ports"] if "in_ports" in data else None,
                         data["out_ports"] if "out_ports" in data else None)
        self.nodes = [Node.class_map[node["name"]] for node in data["nodes"]]
        self.parse_edges(data["edges"])
