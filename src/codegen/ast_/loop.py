#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator loop
"""
from ..node import Node
from ..cpp.cpp_codegen import CppBlock, cpp_eval, CppVariable


class LoopExpression(Node):

    def to_cpp(self, block: CppBlock):
        result = CppVariable(self.out_ports[0].label,
                             self.out_ports[0].type.cpp_type)
        self.out_ports[0].value = result
        self.range_gen.to_cpp(loop_object=self, block=block)


class Condition(Node):
    pass


class PreCondition(Condition):
    pass


class PostCondition(Condition):
    pass


class Body(Node):
    pass


class Init(Node):
    pass


class Returns(Node):
    pass


class Reduction(Node):
    pass


class OldValue(Node):
    pass


class RangeGen(Node):
    # for (auto&& element: array) {
    #     v.append(element);
    # }
    def to_cpp(self, loop_object: LoopExpression, block: CppBlock):
        pass

class Scatter(Node):
    pass
