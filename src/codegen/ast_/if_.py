#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node
from ..edge import Edge


class If(Node):

    def to_cpp(self, scope, indent):

        #for i_p in self.in_ports:
            #print(Edge.edge_to)
        #for e in Edge.edges:
            #print(e)
        print(self.branches[0].__dict__)



class Branch(Node):
    pass


class Condition(Node):
    pass
