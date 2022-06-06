#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Contains functions for source code parsing.
Node module methods are called to make class instances.
"""

import os
from .annotations import rule_annotation
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.exceptions import ParseError
# from parsimonious.exceptions import IncompleteParseError
from .node import Node

from .parser_state import reset

# from .ast_.identifier import Identifier
# from .ast_ import function.Function, identifier.Identifier
from .ast_ import *
from .error import SisalError

from .edge import Edge
from .type import SingularType, IntegerType, BooleanType, RealType, MultiType


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
        return function.Function(
            function_name=vc_[2].name,
            args=vc_[6],
            retvals=vc_[8],
            body=vc_[12],
            location=self.get_location(node),
        )

    def visit_call(self, node, vc_):
        """function call visitor"""
        return call.Call(
            name=vc_[1].name, args=vc_[5], location=self.get_location(node)
        )

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

    def visit_type(self, node, vc_):
        """type visitor"""
        return vc_[0]

    def visit_std_type(self, node, vc_):
        """type visitor"""
        return vc_[0]

    def visit_integer_type(self, node, _):
        """type visitor"""
        return IntegerType(self.get_location(node))

    def visit_real_type(self, node, _):
        """type visitor"""
        return RealType(self.get_location(node))

    def visit_boolean_type(self, node, _):
        """type visitor"""
        return BooleanType(self.get_location(node))

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
        location = self.get_location(node)
        return literal.Literal(
            type_=IntegerType(location=location),
            value=node.text,
            location=location,
        )

    def visit_number_literal_real(self, node, vc_):
        """literal visitor"""
        location = self.get_location(node)
        return literal.Literal(
            type_=RealType(location=location),
            value=node.text,
            location=self.get_location(node),
        )

    def visit_if(self, node, vc_):
        """if visitor"""
        condition_nodes = [vc_[2]]
        then_nodes = vc_[6]

        if type(vc_[9]) == list:
            else_nodes = vc_[9][0][3]
        else:
            else_nodes = []

        elseif = []

        for n, e in enumerate(vc_[8]):
            condition_nodes.append(e[2])
            elseif.append(e[6])

        locations = ", ".join([condition.location for condition in condition_nodes])

        return if_.If(
            multi_exp.MultiExp(condition_nodes, locations),
            then_nodes,
            elseif,
            else_nodes,
            self.get_location(node),
        )

    def visit_algebraic(self, node, vc_):
        """algebraic visitor"""
        expression = [vc_[0]]
        if len(vc_):
            for n, v in enumerate(vc_[1]):
                expression += [v[1]] + [v[3]]
        return algebraic.Algebraic(
            expression=expression, location=self.get_location(node)
        )

    def visit_brackets_algebraic(self, node, vc_):
        """brackets algebraic visitor"""
        return vc_[2]

    def visit_operand(self, node, vc_):
        """operand visitor"""
        return vc_[0]

    def visit_bin_op(self, node, vc_):
        """operand visitor"""
        return algebraic.Bin(operator=node.text, location=self.get_location(node))

    @staticmethod
    def visit_module(_, vc_):
        """module visitor"""
        functions = [func[1] for func in vc_[0]]

        return functions

    def visit_multi_exp(self, node, vc_):
        """multi_exp visitor"""
        return multi_exp.MultiExp(
            expressions=[vc_[0]] + [v[3] for v in vc_[1]],
            location=self.get_location(node),
        )

    @staticmethod
    def visit_exp_singular(_, vc_):
        """exp_singular visitor"""
        return vc_[0]

    @staticmethod
    def visit_def(_, vc_):
        """exp_singular visitor"""
        return vc_[0]

    @staticmethod
    def generic_visit(node, visited_children):
        """generic visitor"""
        return visited_children or node


grammar_file_name = os.path.dirname(os.path.realpath(__file__)) +\
                    "/module_grammar.ini"

with open(grammar_file_name, "r", encoding="UTF-8") as gr_file:
    grammar_text = gr_file.read()

grammar = Grammar(grammar_text)
module_visitor = ModuleVisitor()


def parse(src_code: str) -> dict:
    """Parses provided source code and returns an IR.
    The returned value is a dict that can be exported as JSON"""

    reset()

    try:
        parsed = grammar.parse(src_code)
        functions = module_visitor.visit(parsed)
        for function in functions:
            function.build()
        functions = [function.ir_() for function in functions]
        return {"functions": functions}
    except Exception as e:
        if type(e) == ParseError:
            wrong = e.text[e.pos: e.pos + 20].split(" ")[0]
            print(
                f"Syntax error ({e.line()}:{e.column()}): ",
                rule_annotation(e.expr.name),
                # e.expr.as_rule(),
                f'expected instead of "{wrong}" at {e.line()}:{e.column()}: '
                + '"'
                + e.text[int(e.pos): e.pos + 20].split("\n")[0]
                + '"',
            )
        elif type(e) == SisalError:
            print(e)
        else:
            print("unknown error")
            raise Exception(e)
        return None
