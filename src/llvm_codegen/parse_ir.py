#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node parsing
"""

from .ast_ import (
    function,
    array_access,
    call,
    arith,
    common,
    if_,
    let,
    literal,
    array_init,
    loop,
    record_access,
    record_init,
)
from .node import Node
from .type import get_type

# from .timeout import process_timeout

class_map = {
    "Lambda": function.Function,
    "If": if_.If,
    "Else": if_.Branch,
    "ElseIf": if_.Branch,
    "Then": if_.Branch,
    "Branch": if_.Branch,
    "Condition": if_.Condition,
    "Binary": arith.Binary,
    "Unary": arith.Unary,
    "FunctionCall": call.FunctionCall,
    "Literal": literal.Literal,
    "LoopExpression": loop.LoopExpression,
    "Init": common.Init,
    "PreCondition": loop.PreCondition,
    "PostCondition": loop.PostCondition,
    "Body": loop.Body,
    "Returns": loop.Returns,
    "OldValue": loop.OldValue,
    "Reduction": loop.Reduction,
    "ArrayAccess": array_access.ArrayAccess,
    "BuiltInFunctionCall": call.FunctionCall,
    "Let": let.Let,
    "RangeGen": loop.RangeGen,
    "Range": loop.RangeNumeric,
    "Scatter": loop.Scatter,
    "ArrayInit": array_init.ArrayInit,
    "RecordInit": record_init.RecordInit,
    "RecordAccess": record_access.RecordAccess,
}

Node.class_map = class_map


def parse_node(node):
    class_map[node["name"]](node)


def parse_definition():
    pass


def parse_ir(ir_data):
    for fn_ in ir_data["functions"]:
        parse_node(fn_)
    definitions = {}
    if "definitions" in ir_data:
        for def_ in ir_data["definitions"]:
            definitions[def_["name"]] = get_type(def_["type"])

    # process_timeout()

    return function.Function.functions, definitions
