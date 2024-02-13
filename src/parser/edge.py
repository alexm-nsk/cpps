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
from .error import SisalError
from .type import IntegerType, RealType, AnyType, ArrayType


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
        """Resets edge indices"""
        cls.__edges__ = []
        cls.__edges_from__ = {}
        cls.__edges_to__ = {}

    def __post_init__(self):
        """Runs after dataclasses __init__"""
        if self.to.type is None:
            self.to.type = self.from_.type

        from_type = type(self.from_.type)
        to_type = type(self.to.type)

        if from_type == AnyType or (
            from_type == ArrayType and type(self.from_.type.element) == AnyType
        ):
            self.from_.type = self.to.type

        if ((from_type != to_type) and
           not (from_type == AnyType or to_type == AnyType)):
            """Do a type compatibility check"""
            if from_type in [IntegerType, RealType] and to_type in [
                IntegerType,
                RealType,
            ]:
                from .parser_state import add_warning

                add_warning(
                    f"{from_type} and {to_type} combination "
                    f"({self.from_.node().location} and "
                    f"{self.to.node().location})"
                    ": possible loss of data"
                )

            else:

                extra = ""

                if type(self.to.node()).__name__ == "Function":
                    extra = (
                        f" (Function's ({self.to.node().function_name}) "
                        "return type doesn't match returned type)"
                    )
                raise SisalError(
                    f"Type mismatch{extra}: "
                    f"{from_type.__name__} at "
                    f"{self.from_.type.location} and "
                    f"{to_type.__name__} at "
                    f"{self.from_.type.location}",
                    location=f"{self.from_.type.location}",
                )

        Edge.__edges__.append(self)
        Edge.__edges_from__[self.from_.node_id] = self
        Edge.__edges_to__[self.to.node_id] = self

    def ir_(self):
        """An IR form of this edge as a dict"""
        if PORT_FULL_DESCRIPTION_IN_EDGES:
            return [self.from_.ir_(), self.to.ir_()]
        else:
            return dict(
                from_=(self.from_.node_id, self.from_.index),
                to=(self.to.node_id, self.to.index),
            )

    def gml(self):
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

        gml_str = (
            f'<edge source="{self.from_.node().id}" '
            f'target="{self.to.node().id}" '
            f'sourceport="{src_port_type}{self.from_.index}" '
            f'targetport="{dst_port_type}{self.to.index}">\n'
            f"{GraphMlModule.indent(type_str)}"
            "\n</edge>"
        )
        return gml_str
