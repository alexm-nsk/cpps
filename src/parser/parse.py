#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Contains functions for source code parsing.
Node module methods are called to make class instances.
"""

import os
import re
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.exceptions import ParseError, VisitationError

from .annotations import rule_annotation
from .parser_state import (reset,
                           get_warnings,
                           debug_enabled,
                           get_definition,
                           add_definition)
# from .statement import Assignment, MultiAssignment
from .statement import MultiAssignment
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
    array_init,
    record_init,
    record_access
)
from .error import SisalError
from .type import (
    IntegerType, BooleanType, RealType, ArrayType, TypeDefinition, RecordType)
from .pre_check import pre_check
from .known_pragmas import known_pragmas


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
    '''
    pragmas = ("/?" _ pragma _)*
    pragma = pragma_name _ "(" _ pragma_args _ ")"
    pragma_name = ~"[a-z_][a-z0-9_]*"i
    pragma_args = pragma_arg ( _ "," _ pragma_arg)*
    pragma_arg = ~"[a-z0-9_]*"i
    '''
    @staticmethod
    def is_empty_node(node):
        if type(node) == list:
            return False
        else:
            if node.text!="":
                return False
        return True

    def visit_pragma(self, node, vc_):
        name = vc_[0]
        location = self.get_location(node)
        if name not in known_pragmas:
            raise SisalError(
                f"unknown pragma: \"{name}\" at {location}", location)
        args = vc_[2][0][2] if not self.is_empty_node(vc_[2]) else []
        return {"name": name, "args": args}

    def visit_pragmas(self, node, vc_):
        return [v[-2] for v in vc_]

    def visit_pragma_args(self, node, vc_):
        return [vc_[0]] + [v[-1] for v in vc_[-1]]

    def visit_pragma_arg(self, node, _):
        return node.text

    def visit_pragma_name(self, node, _):
        return node.text

    def visit_function(self, node, vc_):
        """function visitor"""
        return function.Function(
            pragmas=vc_[0],
            function_name=vc_[4].name,
            args=vc_[8],
            retvals=vc_[10],
            body=vc_[14],
            location=self.get_location(node),
        )

    def visit_call(self, node, vc_):
        """function call visitor"""
        return call.Call(
            name=vc_[1].name,
            args=self.optional_node(vc_[5]),
            location=self.get_location(node)
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
                if type(group[1]) == identifier.Identifier:
                    type_ = get_definition(group[1].name)
                    type_.type_name = group[1].name
                    type_.custom_type = True
                else:
                    type_ = group[1]

                args.append([arg, type_])
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
        if type(vc_[0]) == identifier.Identifier:
            return get_definition(vc_[0].name)
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

    def visit_literal_boolean(self, node, vc_):
        """literal visitor"""
        location = self.get_location(node)
        return literal.Literal(
            type_=BooleanType(location=location),
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

        locations = ", ".join([
                                condition.location
                                for condition in condition_nodes
                               ])

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

    def visit_open_operand(self, node, vc_):
        """passthrough"""
        return vc_[0]

    def visit_br_operand(self, node, vc_):
        """passthrough"""
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
        functions = []
        definitions = []
        for item in vc_[0]:
            if type(item[1]) == function.Function:
                functions.append(item[1])
            elif type(item[1]) == TypeDefinition:
                definitions.append(item[1].ir_())

        # functions = [func[1] ]

        return functions, definitions

    def visit_record_field(self, node, vc_):
        # record_field=identifier _ ":" _ type
        return vc_[0].name, vc_[-1]

    def visit_record(self, node, vc_):
        fields = {}
        for k, v in [vc_[4]] + [rec[-1] for rec in vc_[5]]:
            fields[k] = v
        return RecordType(location=self.get_location(node), fields=fields)

    def visit_record_init(self, node, vc_):
        # "record" _ "[" _ (identifier _ ":" _ exp _ ";")* _ (identifier _ ":" _ exp) _ "]"
        iterated = (vc_[4] if not self.is_empty_node(vc_[4]) else []) + [vc_[6]]
        fields = dict([(field[0].name, field[4]) for field in iterated])

        return record_init.RecordInit(None, fields)

    # record_field_access= record_exp _ "." _ identifier
    # helps avoid endless recursion:
    # record_f_acc_arr   = array_access _ "." _ identifier
    def visit_record_exp(self, node, vc_):
        return vc_[0]

    def visit_record_field_access(self, node, vc_):
        record = vc_[0]
        field = vc_[-1].name
        # print(record, field)
        return record_access.RecordAccess(record,
                                          field,
                                          self.get_location(node))

    # same for field acces when record is in an array element
    # doing it separately helps avoid grammar recursion
    def visit_record_f_acc_arr(self, node, vc_):
        record = vc_[0]
        field = vc_[-1].name
        # print(record, field)
        return record_access.RecordAccess(record,
                                          field,
                                          self.get_location(node))

    def visit_type_definition(self, node, vc_):
        t_d = TypeDefinition(name=vc_[2].name, type_=vc_[-1])
        t_d
        add_definition(vc_[2].name, t_d.type)
        return t_d

    #                         0    1   2  3     4     5  6
    # bracketed_multiexp = pragmas _ lpar _ multi_exp _ rpar
    def visit_bracketed_m_exp(self, node, vc_):
        # assign groups (keep count)
        # set the pragma to multiexp
        m_exp = vc_[4]
        pragmas = vc_[0]
        if pragmas:
            m_exp.set_pragmas(pragmas)
        return m_exp

    def visit_m_exp(self, node, vc_):
        """multi_exp visitor"""
        return multi_exp.MultiExp(
            expressions=[vc_[0]] + [v[3] for v in vc_[1]],
            location=self.get_location(node),
        )

    def visit_multi_exp(self, node, vc_):
        return vc_[0]

    # Arrays:
    def visit_array_init(self, node, vc_):
        type_definition = self.optional_node(vc_[0])
        if type_definition:
            type_definition = type_definition[0]

        items = [vc_[3]] + [item[3] for item in vc_[4]]

        return array_init.ArrayInit(type_definition,
                                    items,
                                    location=self.get_location(node))

    def visit_array(self, node, vc_):
        return vc_[0]

    def visit_array_of(self, node, vc_):
        return ArrayType(location=self.get_location(node), element=vc_[4])

    def visit_array_br(self, node, vc_):
        return ArrayType(location=self.get_location(node), element=vc_[4])

    def visit_array_access(self, node, vc_):
        return vc_[0]

    def visit_array_access_sep(self, node, vc_):
        return array_access.ArrayAccess(
            array=vc_[0],
            index=[index[3] for index in vc_[1]],
            location=self.get_location(node),
        )

    def visit_array_access_i_list(self, node, vc_):
        return array_access.ArrayAccess(
            array=vc_[0],
            index=[vc_[4]] + [index[2] for index in vc_[6]],
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

    '''
    def visit_assignment(self, node, vc_):
        identifier = vc_[0]
        value = vc_[4]
        return Assignment(identifier, value)
    '''

    def visit_multi_assignment(self, node, vc_):
        # identifier _ (_ "," _ identifier)* _ ":=" _ multi_exp...
        identifiers = [vc_[0]] + [iden_node[-1] for iden_node in vc_[2]]
        values = vc_[6]
        return MultiAssignment(identifiers, values)

    # Loops:

    def visit_while_do(self, node, vc_):
        condition = loop.PreCond(exp=vc_[2], location=vc_[2].location)
        body = loop.LoopBody(
            statements=vc_[6],
            location=self.get_location(node),
        )
        return dict(body=body, condition=condition)

    def visit_do_while(self, node, vc_):
        condition = loop.PostCond(exp=vc_[6], location=vc_[6].location)
        body = loop.LoopBody(statements=vc_[2],
                             location=self.get_location(node))
        return dict(body=body, condition=condition)

    def visit_while_do_while(self, node, vc_):
        condition1 = loop.PreCond(exp=vc_[6], location=self.get_location(node))
        condition2 = loop.PostCond(exp=vc_[6],
                                   location=self.get_location(node))
        body = loop.LoopBody(statements=vc_[2],
                             location=self.get_location(node))
        return dict(body=body, condition=[condition1, condition2])

    def visit_repeat(self, node, vc_):
        return dict(
            body=loop.LoopBody(statements=vc_[2],
                               location=self.get_location(node)),
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
            returns=self.optional_node(vc_[8]),
            location=self.get_location(node),
        )

    def visit_reduction(self, node, vc_):
        optional = self.optional_node(vc_[5])
        when = optional[3] if optional else None
        return loop.Reduction(
            what=vc_[0],
            of_what=vc_[4],
            when=when,
            location=self.get_location(node)
        )

    def visit_reductions(self, node, vc_):
        return [vc_[0]] + [red[3] for red in vc_[1]]

    def visit_reduction_type(self, node, vc_):
        return vc_[0].text

    def visit_returns(self, node, vc_):
        reductions = vc_[2]
        return loop.Returns(reductions, self.get_location(node))

    def visit_old(self, node, vc_):
        return loop.OldValue(identifier=vc_[2],
                             location=self.get_location(node))

    # Ranges:

    def visit_ranges(self, node, vc_):
        return loop.RangeGen(
            ranges=[vc_[0]] + [r[2] for r in vc_[2]],
            location=self.get_location(node)
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
        return vc_[0][2][0]

    @staticmethod
    def visit_def(_, vc_):
        """exp_singular visitor"""
        return vc_[0]

    # Other
    def visit_exp(self, node, vc_):
        node = vc_[2][0]
        node.pragmas = vc_[0]
        return node

    def visit_empty(self, node, _):
        """empty visitor"""
        raise SisalError("Empty expressions are not allowed!",
                         self.get_location(node))

    @staticmethod
    def generic_visit(node, vc_):
        """generic visitor"""
        return vc_ or node


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
        src_code = pre_check(src_code)
        parsed = grammar.parse(src_code)
        functions, definitions = module_visitor.visit(parsed)
        for function_ in functions:
            function_.build()
        #  functions = [function.ir_() for function in functions]
        warnings = get_warnings()

        ret_val = {"functions": functions, "errors": []}

        if warnings:
            ret_val["warnings"] = warnings
        if definitions:
            ret_val["definitions"] = definitions

        return ret_val

    except Exception as e:
        if debug_enabled():
            raise Exception(e)
        if type(e) == ParseError:
            wrong = e.text[e.pos: e.pos + 20].split(" ")[0]
            error_text = (
                f"Syntax error ({e.line()}:{e.column()}): ",
                rule_annotation(e.expr.name),
                # e.expr.as_rule(),
                f'expected instead of "{wrong}" at {e.line()}:{e.column()}: '
                + '"'
                + e.text[int(e.pos): e.pos + 20].split("\n")[0]
                + '"',
            )
            return {"functions": [],
                    "errors": [f"Internal Error: {error_text}"]}
        elif type(e) == SisalError:
            return {"functions": [], "errors": [str(e)]}
        elif type(e) == VisitationError:
            # TODO do it properly:
            message = str(e)
            message = re.sub("Parse tree:.*", "", message, flags=re.DOTALL)
            print(message)
        else:
            return {"functions": [], "errors": ["internal error:" + str(e)]}
        return {"functions": [], "errors": [f"Internal Error: {str(e)}"]}
