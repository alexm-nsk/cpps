"""module optimizations"""
import sys

sys.path.append("..")

from ir.module import Module
from ir.ast_.literal import Literal
from ir.edge import Edge
from ir.type import IntegerType


operators = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
}


def printm(module):
    import json

    print(json.dumps(module.save_to_json(), indent=2))


def optimize_ir(module: Module):
    # iterate over all IF nodes:

    for if_node in module.get_nodes("If"):
        output_node = if_node.condition.out_ports[0].input_node
        if type(output_node) is Literal and output_node.value==True:
            module.swap_complex_node(if_node.branches[0], if_node)
            break

    # iterate over all binary nodes:
    for bin in module.get_nodes("Binary"):
        # get left and right operand nodes:
        # ("input_node" is the node attached to the port with an edge)
        left = bin.in_ports[0].input_node
        right = bin.in_ports[1].input_node
        # check if both operators are literals:
        if type(left) is Literal and type(right) is Literal:
            # calculate the result using operator map
            # (see above in this file):
            result = operators[bin.operator](left.value, right.value)
            # ensure the proper type of value:
            result = bin.out_ports[0].type.convert(result)
            # get the node containing the operator and operands nodes:
            parent = bin.parent_node
            # create new literal node to hold the calculated result:
            lit = module.Literal(result, bin.out_ports[0].type, parent)
            # find the edge that transfers the result from the bin:
            edge = bin.out_ports[0].output_edges[0]
            # reattach the origin (which is the "start")
            # to the new node's output:
            edge.attach_origin(lit.out_ports[0])
            # delete the no longer necessary nodes:
            module.delete_node(left, True)
            module.delete_node(right, True)
            module.delete_node(bin, True)

    return module
