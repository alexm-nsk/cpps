#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loops
"""

from ..node import Node, build_method
from ..edge import Edge
from ..port import Port
from ..statement import Statement
from ..scope import SisalScope
from ..sub_ir import SubIr
from ..type import IntegerType, StreamType, BooleanType, ArrayType
from .literal import Literal
from ..error import SisalError


class Cond(Node):
    """Loop condition node, base class"""

    def __init__(self, exp, location: str):
        super().__init__(location)
        self.exp = exp
        # copies the name from class, see PreCond/ PostCond
        self.name = self.name

    def build(self, scope: SisalScope):
        loop = scope.node
        out_port = Port(self.id, BooleanType(), 0, "condition_output")
        self.out_ports = [out_port]
        self.copy_ports(loop, out=False)

        if "init" in loop.__dict__:
            self.copy_results_ports(loop.init)
        if "range_gen" in loop.__dict__:
            self.copy_results_ports(loop.range_gen)
        if "body" in loop.__dict__:
            self.copy_results_ports(loop.body)

        scope = SisalScope(self)
        self.add_sub_ir(self.exp.build([out_port], scope))
        del self.exp


class PreCond(Cond):

    name = "Pre Condition"


class PostCond(Cond):

    name = "Post Condition"


class LoopBody(Node):
    """Loop body node, it also forms loop condition object"""

    def __init__(self, statements: list[Statement], location: str):
        super().__init__(location)
        self.name = "Loop Body"
        self.statements = statements
        self.in_ports = []

    def setup_ports(self, scope: SisalScope):
        loop = scope.node
        self.copy_ports(loop, out=False)

        if loop.init:
            self.copy_results_ports(loop.init)

        if loop.range_gen:
            self.copy_results_ports(loop.range_gen)

    def build(self, scope):
        self.setup_ports(scope)
        scope = SisalScope(self)

        self.out_ports = [
            Port(self.id, None, index, exp.identifier.name)
            for index, exp in enumerate(self.statements)
        ]

        for index, definition in enumerate(self.statements):
            self.add_sub_ir(definition.value.build([self.out_ports[index]], scope))
            # here we add newly defined value to the scope
            value_port = Edge.src_port(self.out_ports[index])
            # TODO add option to not change port's label and rather
            # change it in the scope's copy of the port
            value_port.label = definition.identifier.name
            scope.add_port(value_port)

        del self.statements


class Scatter(Node):
    """Iterates over an iterable type"""

    def __init__(self, iterable, location):
        super().__init__(location)
        self.iterable = iterable
        self.name = "Scatter"

    def num_in_ports(self):
        return 1

    def num_out_ports(self):
        return 2

    @build_method
    def build(self, target_ports: list[Port], scope):
        self.in_ports = [Port(self.id, None, 0)]
        iterable_ir = self.iterable.build([self.in_ports[0]], scope)
        element_type = self.in_ports[0].port_type()
        self.out_ports = [
            Port(self.id, StreamType(element=element_type), 0, "element"),
            Port(self.id, IntegerType(), 1, "index"),
        ]
        del self.iterable
        return SubIr([self], [], []) + iterable_ir


class RangeNumeric(Node):
    """Numeric range, iterated over by Scatter"""

    def __init__(self, left, right, location: str):
        super().__init__(location)
        self.name = "Range"
        self.left = left
        self.right = right
        self.out_ports = [Port(self.id, IntegerType(), 0, "range output")]
        self.in_ports = [
            Port(self.id, IntegerType(), 0, "left boundary"),
            Port(self.id, IntegerType(), 1, "right boundary"),
        ]

    @build_method
    def build(self, target_ports: list[Port], scope):
        left_ir = self.left.build([self.in_ports[0]], scope)
        right_ir = self.right.build([self.in_ports[1]], scope)
        del self.left
        del self.right
        return SubIr([self], [], []) + left_ir + right_ir


class Range(Node):
    """(Helper node, deleted in second pass) A single range"""

    no_id = True

    def __init__(self, identifier, scatter_node):
        self.identifier = identifier
        self.scatter_node = scatter_node

    def build(self, range_gen_scope: SisalScope) -> SubIr:
        # add ports corresponding to this range to parent
        # RangeGen node
        range_gen = range_gen_scope.node
        index = len(range_gen.out_ports)
        new_value_port = Port(range_gen.id, None, index, label=self.identifier.name)
        new_index_port = Port(
            range_gen.id,
            IntegerType(),
            index + 1,
            label=self.identifier.name + "_index",
        )
        range_gen.out_ports += [new_value_port, new_index_port]
        retval = self.scatter_node.build(range_gen.out_ports, range_gen_scope)
        new_value_port.type.location = self.identifier.location
        return retval


class RangeGen(Node):
    """RangeGen node"""

    def __init__(self, ranges: list[Range], location: str):
        super().__init__(location)
        self.ranges = ranges
        self.name = "RangeGen"
        self.out_ports = []

    def build(self, scope):
        self.copy_ports(scope.node, out=False)
        scope = SisalScope(self)
        for n, range_ in enumerate(self.ranges):
            self.add_sub_ir(range_.build(scope))
        del self.ranges


class Reduction(Node):
    """Reduction segment"""

    def __init__(self, what, of_what, when, location):
        super().__init__(location)
        self.what = what
        self.of_what = of_what
        self.when = when

    def num_out_ports(self):
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope):
        self.operator = self.what
        # create out-port without type specified (it's done later)
        out_port = Port(self.id, None, 0, "reduction output")
        self.out_ports = [out_port]
        cond_port = Port(self.id, BooleanType(), 0, "reduction cond input")
        value_port = Port(self.id, None, 1, "reduction value input")
        self.in_ports = [cond_port, value_port]
        value_ir = self.of_what.build([value_port], scope)
        # if there is no condition for Reduction
        # make a Literal node with "True" value
        # and connect it to cond input,
        # otherwise, apply second pass to the "when" exp
        if self.when:
            cond_ir = self.when.build([cond_port], scope)
        else:
            true_literal = Literal(BooleanType(), value=True)
            true_literal_edge = Edge(true_literal.out_ports[0], cond_port)
            cond_ir = SubIr([true_literal], [], [true_literal_edge])

        if self.operator == "array":
            out_port.type = ArrayType(value_port.type)
        elif self.operator in ["value", "sum"]:
            out_port.type = value_port.type

        # TODO it must be "array", "value", etc
        # out_port.type = value_port.type
        # cleanup (no loger needed after 2nd pass):
        del self.what
        del self.of_what
        del self.when
        return SubIr([self], [], []) + value_ir + cond_ir


class Returns(Node):
    """Returns (or Ret as it's called in Sisal 3.1)"""

    def __init__(self, reduction_segments: list[Reduction], location):
        super().__init__(location)
        self.name = "Returns"
        self.reduction_segments = reduction_segments
        self.out_ports = []

    def build(self, scope):
        loop = scope.node
        if loop.num_out_ports() != len(self.reduction_segments):
            raise SisalError("Number of reductions must "
                             "match the expected number of output values"
                             f"({loop.num_out_ports()} expected, "
                             f"got {len(self.reduction_segments)}")
        # in-ports are copied from Loop Expression in-ports
        # and out-ports of init and range_gen
        self.copy_ports(scope.node, out=False)
        if "init" in loop.__dict__:
            self.copy_results_ports(loop.init)
        if "range_gen" in loop.__dict__:
            self.copy_results_ports(loop.range_gen)
        if "body" in loop.__dict__:
            self.copy_results_ports(loop.body)
        # out-ports are dedicated to each reduction
        scope = SisalScope(self)
        # apply 2nd pass to all reductions and create ports for them:
        for index, r_s in enumerate(self.reduction_segments):
            self.out_ports += [Port(self.id,
                                    None,
                                    index,
                                    "reduction #" + str(index))]
            # add processed reduction expressions to this node:
            self.add_sub_ir(r_s.build([self.out_ports[-1]], scope))
            # set loop's out-port type to reduction out-port type:
            loop.out_ports[index].type = self.out_ports[-1].type
        del self.reduction_segments


class Loop(Node):
    """Node describing loops"""

    connect_parent = True
    copy_scope_ports = True

    def __init__(self, range_gen, init, body, condition, reduction, location):
        super().__init__(location)
        self.name = "Loop Expression"
        self.in_ports = []
        self.out_ports = []
        self.init = init
        self.range_gen = range_gen
        self.body = body
        self.condition = condition
        if type(condition) == list:
            # TODO implement while-do-while
            raise SisalError("While-do-while not implemented", location)
        # TODO rename reduction to ret?
        self.reduction = reduction

    def num_out_ports(self):
        return 1

    @build_method
    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:
        scope = SisalScope(self)
        for item in ["init", "range_gen", "body", "condition", "reduction"]:
            if self.__dict__[item]:
                self.__dict__[item].build(scope)
            else:
                del self.__dict__[item]

        return SubIr([self], [], [])
