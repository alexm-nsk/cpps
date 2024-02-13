#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port for code generator
"""

from .type import Type
from itertools import count
from .error import CodeGenError


class Port:

    __ids__ = count()

    def __init__(self, node, type: Type, index, label, in_port: bool):
        self.node = node
        self.type = type
        self.index = index
        self.label = label
        self.id = next(Port.__ids__)
        self.value = None
        self.renamed = False  # set it to True when renamed
        self.in_port = in_port  # shows if is it an in-port

    def __repr__(self):
        return (
            f"Port<{self.node}, {self.index}, {self.label}"
            f", {self.type}, {self.value}>"
        )


def copy_port_values(src_ports, dst_ports):
    """ Copy C++ values assigned to source ports to matching destination ports.
    Ex. If a new variable is defined in Init or LoopBody, we expect it to be
    available in Returns"""
    for d_p in dst_ports:
        try:
            d_p.value = next(s_p.value for s_p in src_ports if s_p.label == d_p.label)
        except:
            # print(d_p.label, d_p.node)
            # print(list(s_p.label for s_p in src_ports))
            # print()
            pass


def copy_port_values_explicit(src_ports, dst_ports):
    """ Copy C++ values assigned to source ports to matching destination ports.
    Ex. If a new variable is defined in Init or LoopBody, we expect it to be
    available in Returns"""
    for index, (src, dst) in enumerate(zip(src_ports, dst_ports)):
        if src.label != dst.label:
            raise CodeGenError(f"mismatch between port labels: {src.id}"
                               f" and {dst.id} {src.label} {dst.label} "
                               f"{src.node} {dst.node}"
                               f"port number {index}",
                               src.type.location)
        dst.value = src.value


def copy_port_labels(src_ports, dst_ports):
    for src, dst in zip(src_ports, dst_ports):
        dst.label = src.label
