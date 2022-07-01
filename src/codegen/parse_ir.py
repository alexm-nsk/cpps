#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node parsing
"""

from .ast_ import function, array, call, alg, common, if_, let, literal, loop
from .node import Node

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
    "ArrayAccess": array.ArrayAccess,
    "BuiltInFunctionCall": call.BuiltInFunctionCall,
    "Let": let.Let,
    "RangeGen": loop.RangeGen,
    "Scatter": loop.Scatter,
}

Node.class_map = class_map


def parse_node(node):
    class_map[node["name"]](node)


def parse_ir(ir_data):
    for fn_ in ir_data["functions"]:
        parse_node(fn_)

    for key in sorted(Node.node_index):
        print(key, Node.node_index[key])
