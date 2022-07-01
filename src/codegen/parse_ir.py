from dataclasses import dataclass
from .ast_ import (function,
                   array,
                   call,
                   alg,
                   common,
                   if_,
                   let,
                   literal,
                   loop)
from .node import Node


class_map = {
    "Lambda": function.Function,
    "If": if_.If,
    "Else": if_.Branch,
    "ElseIf": if_.Branch,
    "Then": if_.Branch,
    "Condition": if_.Condition,
    "Binary": alg.Binary,
    "FunctionCall": call.FunctionCall,
    "Literal": literal.Literal,
    "LoopExpression": loop.LoopExpression,
    "Init": common.Init,
    "PreCondition": loop.PreCondition,
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

nodes = {}





def parse_node(node):
    nodes[node["id"]] = class_map[node["name"]](node)


def parse_ir(ir_data):
    for fn_ in ir_data["functions"]:
        parse_node(fn_)
