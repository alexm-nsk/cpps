#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Contains functions for source code parsing.
Node module methods are called to make class instances.
"""

import os
import sys
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

# from parsimonious.exceptions import ParseError
from .node import Node

# from .ast_.function import Function
# from .ast_.identifier import Identifier
# from .ast_ import function.Function, identifier.Identifier
from .ast_ import *

from .edge import Edge
from .type import SingularType, MultiType


class ModuleVisitor(NodeVisitor):
    """Walks the parsed syntax tree"""

    @staticmethod
    def get_location(node):
        """Returns formatted location of a syntax-node"""
        text = node.full_text

        start_row = text[: node.start].count("\n") + 1
        start_column = len((text[: node.start].split("\n"))[-1])

        end_row = text[: node.end].count("\n") + 1
        end_column = len((text[: node.end].split("\n"))[-1])

        return f"{start_row}:{start_column}-{end_row}:{end_column}"

    def visit_function(self, node, vc_):
        """function visitor"""
        name = vc_[2].name
        args = vc_[6]  # go as pairs [identifier, type_name]
        retvals = vc_[8]
        body = vc_[12]
        return function.Function(name, args, retvals, body, self.get_location(node))

    @staticmethod
    def visit_function_arguments(_, vc_):
        """function_arguments visitor"""
        return vc_[0]

    @staticmethod
    def visit_type_list(_, vc_):
        """visit_type_list visitor"""
        return [vc_[0]] + [v[3] for v in vc_[1]]

    @staticmethod
    def visit_args_groups_list(_, vc_):
        """visitor"""
        args = []
        for group in [vc_[0]] + [v[3] for v in vc_[1]]:
            for arg in group[0]:
                args.append([arg, group[1]])
        return args

    @staticmethod
    def visit_arg_def_group(_, vc_):
        """visitor"""
        return [vc_[0], vc_[4]]

    @staticmethod
    def visit_function_retvals(node, vc_):
        """function_retvals visitor"""
        if node.text:
            return vc_[0][2]
        return None

    def visit_type(self, node, _):
        """type visitor"""
        return SingularType(self.get_location(node), node.text)

    @staticmethod
    def visit_arg_def_list(_, vc_):
        """arg_def_list visitor"""
        return [vc_[0]] + [v[3] for v in vc_[1]]

    def visit_identifier(self, node, _):
        """identifier visitor"""
        return identifier.Identifier(node.text, self.get_location(node))

    def visit_number_literal(self, node, vc_):
        """literl visitor (passthrough)"""
        return vc_[0]

    def visit_number_literal_int(self, node, vc_):
        """literl visitor"""
        return literal.Literal(
            type_=SingularType(name="Integer"),
            value=node.text,
            location=self.get_location(node),
        )

    def visit_number_literal_real(self, node, vc_):
        """literal visitor"""
        return literal.Literal(
            type_=SingularType(name="Real"),
            value=node.text,
            location=self.get_location(node),
        )

    def visit_if(self, node, vc_):
        """if visitor"""
        condition_nodes = vc_[2]
        then_nodes = vc_[6]

        if type(vc_[9]) == list:
            else_nodes = vc_[9][0][3]
        else:
            else_nodes = []

        elseif = []

        for n, e in enumerate(vc_[8]):
            condition_nodes.append(e[2][0])
            elseif.append(e[6])

        return if_.If(
            condition_nodes, then_nodes, elseif, else_nodes, self.get_location(node)
        )

    def visit_algebraic(self, node, vc_):
        """algebraic visitor"""

    def visit_opernad(self, node, vc_):
        """operand visitor"""

    @staticmethod
    def visit_module(_, vc_):
        """module visitor"""
        functions = [def_[0][1].ir_() for def_ in vc_]
        return {"functions": functions}

    @staticmethod
    def visit_exp(_, vc_):
        """exp visitor"""
        return vc_[0] + [v[3][0] for v in vc_[1]]

    @staticmethod
    def visit_exp_singular(_, vc_):
        """exp_singular visitor"""
        return vc_[0]

    @staticmethod
    def generic_visit(node, visited_children):
        """generic visitor"""
        return visited_children or node


grammar_file_name = os.path.dirname(os.path.realpath(__file__)) + "/module_grammar.ini"

with open(grammar_file_name, "r", encoding="UTF-8") as gr_file:
    grammar_text = gr_file.read()
    grammar = Grammar(grammar_text)
    module_visitor = ModuleVisitor()


def parse(src_code: str) -> dict:
    """Parses provided source code and returns an IR.
    The returned value is a dict that can be exported as JSON"""

    Edge.reset()
    Node.reset()
    ir_ = module_visitor.visit(grammar.parse(src_code))

    return ir_
