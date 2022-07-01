#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node
"""
from .port import Port
from .type import Type


class Node:
    def parse_edges(edges):
        pass

    @staticmethod
    def parse_port(port):
        return Port(
            port["node_id"],
            Type(port["type"]),
            port["index"],
            port["label"] if "label" in port else None,
        )

    def parse_ports(self, in_ports, out_ports):
        self.in_ports = [self.parse_port(port) for port in in_ports]
        self.out_ports = [self.parse_port(port) for port in out_ports]

        pass

    def __init__(self, data):
        self.name = data["name"]
        self.parse_ports(data["in_ports"], data["out_ports"])


