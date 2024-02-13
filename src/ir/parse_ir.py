#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node parsing
"""

from .ast_ import (
    function,
    array_access,
    call,
    alg,
    common,
    if_,
    let,
    literal,
    loop,
    array_init,
    record_access,
    record_init,
)
from .node import Node
from .type import get_type

class_map = {
    "Lambda": function.Function,
    "If": if_.If,
    "Else": if_.Branch,
    "ElseIf": if_.Branch,
    "Then": if_.Branch,
    "Branch": if_.Branch,
    "Condition": if_.Condition,
    "Binary": alg.Binary,
    "Unary": alg.Unary,
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
    "BuiltInFunctionCall": call.BuiltInFunctionCall,
    "Let": let.Let,
    "RangeGen": loop.RangeGen,
    "Range": loop.RangeNumeric,
    "Scatter": loop.Scatter,
    "ArrayInit": array_init.ArrayInit,
    "RecordInit": record_init.RecordInit,
    "RecordAccess": record_access.RecordAccess,
}

Node.class_map = class_map


def parse_node(node, module):
    return class_map[node["name"]].load_from_data(node, module)


def parse_definition():
    pass
