#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Contains functions for source code parsing.
Node module methods are called to make class instances.
"""

import os
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.exceptions import ParseError

from .annotations import rule_annotation
from .parser_state import reset
from .statement import Assignment
from .ast_ import (
    algebraic,
    array_access,
    call,
    common,
    function,
    identifier,
    if_,
    let,
    literal,
    loop,
    multi_exp,
)
from .error import SisalError
from .type import IntegerType, BooleanType, RealType, ArrayType


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

    # Functions:

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

    @staticmethod
    def visit_arg_def_list(_, vc_):
        """arg_def_list visitor"""
        return [vc_[0]] + [v[3] for v in vc_[1]]

    # Types:

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

    def visit_identifier(self, node, _):
        """identifier visitor"""
        return identifier.Identifier(node.text, self.get_location(node))

    # Number literals

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

    # If

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

    # Unary

    def visit_unary(self, node, vc_):
        operator = vc_[0]
        value = vc_[2]
        return algebraic.Unary(
            operator.text, value, location=self.get_location(operator)
        )

    def visit_unary_op(self, node, vc_):
        """passthrough"""
        return vc_[0]

    # Algebraic

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
        """passthrough"""
        return vc_[0]

    def visit_bin_op(self, node, vc_):
        """operand visitor"""
        return algebraic.Bin(operator=node.text,
                             location=self.get_location(node))

    def visit_equation(self, node, vc_):
        expression = [
            vc_[0],
            algebraic.Bin(operator=vc_[2].text,
                          location=self.get_location(vc_[2])),
            vc_[4],
        ]
        return algebraic.Algebraic(expression,
                                   location=self.get_location(node))

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

    # Arrays:

    def visit_array(self, node, vc_):
        return vc_[0]

    def visit_array_of(self, node, vc_):
        return ArrayType(location=self.get_location(node), element=vc_[4])

    def visit_array_br(self, node, vc_):
        return ArrayType(location=self.get_location(node), element=vc_[4])

    def visit_array_access(self, node, vc_):
        return array_access.ArrayAccess(
            array=vc_[0],
            index=[index[3] for index in vc_[1]],
            location=self.get_location(node),
        )

    # Let:

    def visit_let(self, node, vc_):
        init = vc_[2]
        body = vc_[6]
        return let.Let(init=init, body=body, location=self.get_location(node))

    # Statements:

    @staticmethod
    def visit_statement(_, vc_):
        """passthrough"""
        return vc_[0]

    def visit_statements(self, node, vc_):
        statements = [statement[0] for statement in vc_]
        return statements

    def visit_assignment(self, node, vc_):
        identifier = vc_[0]
        value = vc_[4]
        return Assignment(identifier, value)

    # Loops:

    def visit_while_do(self, node, vc_):
        condition = loop.PreCond(exp=vc_[2], location=self.get_location(node))
        body = loop.LoopBody(
            statements=vc_[6],
            location=self.get_location(node),
        )
        return dict(body=body, condition=condition)

    def visit_do_while(self, node, vc_):
        condition = loop.PostCond(exp=vc_[6], location=self.get_location(node))
        body = loop.LoopBody(statements=vc_[2], location=self.get_location(node))
        return dict(body=body, condition=condition)

    def visit_while_do_while(self, node, vc_):
        condition1 = loop.PreCond(exp=vc_[6], location=self.get_location(node))
        condition2 = loop.PostCond(exp=vc_[6], location=self.get_location(node))
        body = loop.LoopBody(statements=vc_[2], location=self.get_location(node))
        return dict(body=body, condition=[condition1, condition2])

    def visit_repeat(self, node, vc_):
        return dict(
            body=loop.LoopBody(statements=vc_[2], location=self.get_location(node)),
            condition=None,
        )

    def visit_body(self, node, vc_):
        """passthrough"""
        return vc_[0]

    def optional_node(self, node):
        return node[0] if type(node) == list else None

    def visit_initial(self, node, vc_):
        return common.Init(vc_[2], self.get_location(node))

    def visit_loop(self, node, vc_):
        body_cond = self.optional_node(vc_[6])
        if not body_cond:
            body_cond = dict(body=None, condition=None)
        return loop.Loop(
            range_gen=self.optional_node(vc_[2]),
            init=self.optional_node(vc_[4]),
            body=body_cond["body"],
            condition=body_cond["condition"],
            reduction=self.optional_node(vc_[8]),
            location=self.get_location(node),
        )

    def visit_reduction(self, node, vc_):
        optional = self.optional_node(vc_[5])
        when = optional[3] if optional else None
        return loop.Reduction(
            what=vc_[0], of_what=vc_[4], when=when, location=self.get_location(node)
        )

    def visit_reductions(self, node, vc_):
        return [vc_[0]] + [red[3] for red in vc_[1]]

    def visit_reduction_type(self, node, vc_):
        return vc_[0].text

    def visit_returns(self, node, vc_):
        reductions = vc_[2]
        return loop.Returns(reductions, self.get_location(node))

    # Ranges:

    def visit_ranges(self, node, vc_):
        return loop.RangeGen(
            ranges=[vc_[0]] + [r[2] for r in vc_[2]], location=self.get_location(node)
        )

    def visit_range(self, node, vc_):
        # extra [0] is because (range_numeric / exp) is a group
        return loop.Range(
            identifier=vc_[0],
            scatter_node=loop.Scatter(
                iterable=vc_[4][0], location=self.get_location(node)
            ),
        )

    def visit_range_numeric(self, node, vc_):
        return loop.RangeNumeric(
            left=vc_[0],
            right=vc_[4],
            location=self.get_location(node),
        )

    # Arrays:

    @staticmethod
    def visit_array_index(_, vc_):
        """passthrough"""
        return vc_[0]

    @staticmethod
    def visit_array_exp(_, vc_):
        """passthrough"""
        return vc_[0]

    @staticmethod
    def visit_exp_singular(_, vc_):
        """exp_singular visitor"""
        return vc_[0]

    @staticmethod
    def visit_def(_, vc_):
        """exp_singular visitor"""
        return vc_[0]

    # Other
    def visit_exp(self, node, vc_):
        return vc_[0]

    def visit_empty(self, node, _):
        """empty visitor"""
        raise SisalError("Empty expressions not allowed!", self.get_location(node))

    @staticmethod
    def generic_visit(node, vc_):
        """generic visitor"""
        return vc_ or node


grammar_file_name = os.path.dirname(os.path.realpath(__file__)) + "/module_grammar.ini"

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
            wrong = e.text[e.pos : e.pos + 20].split(" ")[0]
            print(
                f"Syntax error ({e.line()}:{e.column()}): ",
                rule_annotation(e.expr.name),
                # e.expr.as_rule(),
                f'expected instead of "{wrong}" at {e.line()}:{e.column()}: '
                + '"'
                + e.text[int(e.pos) : e.pos + 20].split("\n")[0]
                + '"',
            )
        elif type(e) == SisalError:
            print(e)
        else:
            print("unknown error")
            # TODO raise if the parameter if set:
            raise Exception(e)
        return None
