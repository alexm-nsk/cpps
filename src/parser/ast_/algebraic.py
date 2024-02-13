#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Algebraic operations, bin node and various tools for those
"""

from ..node import Node, build_method
from ..port import Port
from ..type import IntegerType, RealType, BooleanType, ArrayType

from ..scope import SisalScope
from ..sub_ir import SubIr
from ..error import SisalError


class Unary(Node):
    """Unary operation node"""

    def __init__(self, operator: str, value: Node, location: str):
        super().__init__(location)
        self.operator = operator
        self.value = value
        self.name = "Unary"
        self.in_ports = [Port(self.id,
                              None,
                              0,
                              label=f"unary ({self.operator}) input")]
        self.out_ports = [
            Port(self.id, None, 0, label=f"unary ({self.operator}) output")
        ]

    @build_method
    def build(self, target_ports: list[Port], scope) -> SubIr:
        """returns an IR form of this node (Unary)"""
        value_ir = self.value.build(self.in_ports, scope)
        # set output port type to match in port
        # TODO: check - it might depend on the operator!
        self.out_ports[0].type = self.in_ports[0].type
        del self.value
        return value_ir + SubIr([self], [], [])


class Bin(Node):
    """Binary operation node. Only processed within Algebraic's 'build'
    method"""

    # TODO make a class for different operation groups
    # (sqrt can result in Real, even when arguments are integers)

    alg_type_map = {
        IntegerType: {RealType: RealType, IntegerType: IntegerType},
        RealType: {RealType: RealType, IntegerType: RealType},
        ArrayType: {ArrayType: ArrayType},
    }

    def result_type(self):
        """Returns result type when processing two given types"""
        try:
            if self.operator in ["<", ">", ">=", "<=", "=", "&", "|"]:
                return BooleanType()

            left_type = self.in_ports[0].type
            left_class = type(left_type)
            right_type = self.in_ports[1].type
            right_class = type(right_type)
            class_ = Bin.alg_type_map[left_class][right_class]

            if class_ == ArrayType:  # and left_type == right_type:
                # TODO compare left and right type and return a type
                # otherwise - raise an exception
                return left_type.get_a_copy(location=self.location)

            return class_(location=self.location)

        except KeyError:
            raise SisalError(
                f"Operations {self.operator} between {left_type} and "
                f"{right_type} not implemented. {self.location}"
            )

    def __init__(self, operator: str, location: str):
        super().__init__(location)
        self.operator = operator
        self.name = "Binary"
        self.in_ports = [
            Port(self.id, None, 0, "left"),  # port types will
            Port(self.id, None, 1, "right"),  # be set later
        ]

    def num_out_ports(self):
        """override Node's num_out_ports in case we don't have out_ports yet"""
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope) -> SubIr:
        """returns an IR form of this node (Bin)"""
        self.out_ports = [
            Port(self.id,
                 self.result_type(),
                 0,
                 f"binary output ({self.operator})")
        ]
        return SubIr(nodes=[self], internal_edges=[], output_edges=[])

    def ir_(self):
        retval = super().ir_()
        return retval

    def __repr__(self):
        return f"<Bin: {self.operator}>"


class Algebraic(Node):
    """A class for algebraic calculations.
    Transforms into Bin and operand nodes"""

    no_id = True

    def __init__(self, expression: list, location: str = None):
        super().__init__(location)
        self.expression = expression

    def num_out_ports(self):
        """override Node's num_out_ports in case we don't have out_ports yet"""
        return 1

    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        """Turn algebraic int nodes and edges"""
        # by design we get alternating operands and binary operators
        # super().build(target_ports, scope)

        # low_priority = ["+", "-", "<", ">", ">=", "<="]
        logic = ["&", "|", "||"]
        comp = ["<", ">", ">=", "<=", "~="]
        additive = ["+", "-"]

        def process(operators: list = []):
            """recursively processes parts of algebraic, until only single
            operands left, it's done in reverse,
            so we don't have to flip + and -"""
            for n, item in reversed(list(enumerate(self.expression))):
                if type(item) == Bin and (
                    item.operator in operators or operators == []
                ):
                    if hasattr(self, "pragmas") and self.pragmas:
                        # copy pragmas from this Algebraic to the
                        # root (operator) node
                        item.pragmas = self.pragmas
                        if hasattr(self, "pragma_group"):
                            item.pragma_group = self.pragma_group
                        self.pragmas = None

                    left = self.expression[:n]
                    left = Algebraic(left) if len(left) > 1 else left[0]
                    right = self.expression[n + 1:]
                    right = Algebraic(right) if len(right) > 1 else right[0]
                    # note the order of 'builds' in 'return':
                    # we first need to get left and right built,
                    # then we can set in-port types of bins to
                    # the out-port types of left and right

                    return (
                        left.build([item.in_ports[0]], scope)
                        + right.build([item.in_ports[1]], scope)
                        + item.build([target_ports[0]], scope)
                    )

        return (process(logic) or
                process(comp) or
                process(additive) or
                process())
