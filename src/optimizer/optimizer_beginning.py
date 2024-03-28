import sys

sys.path.append("..")

from ir.module import Module
from ir.edge import Edge
from ir.node import Node
from ir.ast_.literal import Literal
from ir.ast_.call import FunctionCall
from ir.ast_.function import Function
from ir.type import IntegerType, BooleanType
from ir.port import Port

operators = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "**": lambda x, y: x**y,
    ">": lambda x, y: x > y,
    "<": lambda x, y: x < y,
    "=": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    ">=": lambda x, y: x >= y,
    "<=": lambda x, y: x <= y,
    "!": lambda x, y: not y,
    "&": lambda x, y: x and y,
    "|": lambda x, y: x or y,
}


def printm(module):
    import json

    print(json.dumps(module.save_to_json(), indent=2))


def constant_folding_bin(module: Module):
    for bnode in module.get_nodes("Binary"):
        left = bnode.in_ports[0].input_node
        right = bnode.in_ports[1].input_node
        if type(left) is Literal:
            if type(right) is Literal:
                result = operators[bnode.operator](left.value, right.value)
                result = bnode.out_ports[0].type.convert(result)
                parent = bnode.parent_node
                lit = module.Literal(result, bnode.out_ports[0].type, parent)
                bnode.out_ports[0].output_edges[0].attach_origin(lit.out_ports[0])
                module.delete_node(left, True)
                module.delete_node(right, True)
                module.delete_node(bnode, True)
    return module


def sub_bin_cut(module: Module):

    def reduce_to_arg(arg: Node, ind_opp, attach_to_opposite=True):
        # function removing the binary node and it's unnecessary argument
        nonlocal module
        nonlocal bnode
        edge = bnode.out_ports[0].output_edges[0]
        if attach_to_opposite:
            # if the non-literal value is unchanged by the operator (e.g. +0,*1)
            edge.attach_origin(bnode.in_ports[ind_opp].input_edge.from_)
            nodes,inted,inped=arg.trace_back()
            for node in nodes:
                module.delete_node(node, True)
            module.delete_node(arg, True)
        else:
            # if the result is always the same literal (e.g. *0)
            edge.attach_origin(arg.out_ports[0])
            opp = bnode.in_ports[ind_opp].input_node
            nodes,inted,inped=opp.trace_back()
            for node in nodes:
                module.delete_node(node, True)
            module.delete_node(opp, True)
        module.delete_node(bnode, True)

    for bnode in module.get_nodes("Binary"):
        # check for subexpressions that may be reduced
        left = bnode.in_ports[0].input_node
        right = bnode.in_ports[1].input_node
        if type(left) is Literal:
            if left.value == 0:
                if bnode.operator == "+":
                    reduce_to_arg(left, 1)
                elif bnode.operator in ("*", "**", "/"):
                    reduce_to_arg(left, 1, False)
                elif bnode.operator == "-":
                    un = module.Unary("-", bnode.out_ports[0].type, bnode.parent_node)
                    edge = bnode.out_ports[0].output_edges[0]
                    egde.attach_origin(un.out_ports[0])
                    edge = right.out_ports[0].output_edges[0]
                    edge.attach_target(un.in_ports[0])
                    module.delete_node(left, True)
                    module.delete_node(bnode, True)
            elif left.value == 1:
                if bnode.operator == "*":
                    reduce_to_arg(left, 1)
                elif bnode.operator == "**":
                    reduce_to_arg(left, 1, False)
            elif left.value == True:
                if bnode.operator == "+":
                    reduce_to_arg(left, 1, False)
                elif bnode.operator == "*":
                    reduce_to_arg(left, 1)
            elif left.value == False:
                if bnode.operator == "*":
                    reduce_to_arg(left, 1, False)
                elif bnode.operator == "+":
                    reduce_to_arg(left, 1)
        elif type(right) is Literal:
            if right.value == 0:
                if bnode.operator in ("+", "-"):
                    reduce_to_arg(right, 0)
                elif bnode.operator == "*":
                    reduce_to_arg(right, 0, False)
                elif bnode.operator == "**":
                    lit = module.Literal(
                        bnode.out_ports[0].type.convert(1),
                        bnode.out_ports[0].type,
                        bnode.parent_node
                    )
                    edge = bnode.out_ports[0].output_edges[0]
                    egde.attach_origin(lit.out_ports[0])
                    module.delete_node(left, True)
                    module.delete_node(right, True)
                    module.delete_node(bnode, True)
            elif right.value == 1:
                if bnode.operator in ("*", "**", "/"):
                    reduce_to_arg(right, 0)
            elif right.value == True:
                if bnode.operator == "+":
                    reduce_to_arg(right, 0, False)
                elif bnode.operator == "*":
                    reduce_to_arg(right, 0)
            elif right.value == False:
                if bnode.operator == "*":
                    reduce_to_arg(right, 0, False)
                elif bnode.operator == "+":
                    reduce_to_arg(right, 0)
    return module


def constant_folding_if(module: Module):
    for ifnode in module.get_nodes("If"):
        cond = ifnode.condition.out_ports[0].input_node
        if type(cond) is Literal:
            if cond.value == True:
                module.swap_complex_node(ifnode.branches[0], ifnode)
                break
            else:
                if ifnode.branches[1]:
                    module.swap_complex_node(ifnode.branches[1], ifnode)
                    break
    return module


def constant_folding_let(module: Module):
    for letnode in module.get_nodes("Let"):
        body = letnode.body
        init = letnode.init
        for port in init.out_ports:
            # get the origin of a local variable and check if it's literal
            inp = port.input_node
            if type(inp) is Literal:
                # connect nodes using the unnecessary local variable to the literal
                # do the labels of the ports need to be deleted, if the variable they represent is?
                ind = port.index
                for edge in body.in_ports[ind].output_edges:
                    lit = module.Literal(inp.value, port.type, body)
                    egde.attach_origin(lit.out_ports[0])
                # remove the no longer needed literal
                module.delete_node(inp, True)
        # if all the local variables either were literals or are equivalent to the global ones, swap let with it's body
        if not hasattr(init, "nodes"):
            module.swap_complex_node(body, letnode)


def open_substitution(module: Module):
    for fnode in module.get_nodes("Lambda"):
        f = fnode.function_name
        if f != "main":
            i = 0
            for c in module.get_nodes("FunctionCall"):
                if c.callee == f:
                    c1 = c
                    i += 1
            if i == 1:
                if c1.get_containing_function() is not fnode:
                    vars_=[]
                    outs_=[]
                    for port in fnode.in_ports:
                        vars_.append((port.label,port.type))
                    for port in fnode.out_ports:
                        outs_.append((port.label,port.type))
                    parent=c1.parent_node
                    subs=module.Let(parent,vars_,outs_)
                    cnodes,internal_edges,input_edges=c1.trace_back()
                    init=subs.init
                    body=subs.body
                    init.nodes.extend(cnodes)
                    init.edges.extend(internal_edges)
                    if parent.in_ports:
                        for port1,port2,port3 in parent.in_ports, init.in_ports, subs.in_ports:
                            for edge in port1.output_edges:
                                if edge in input_edges:
                                    edge2=Edge(port2,edge.to,init)
                                    #init.edges.append(edge2)
                                    edge.attach_target(port3)
                    if c1.in_ports:
                        for port1, port2 in fnode.in_ports, body.in_ports:
                            for edge in port1.output_edges:
                                edge.attach_origin(port2)
                        for port1,port2 in c1.in_ports,init.out_ports:
                            port1.input_edge.attach_target(port2)
                    body.nodes.extend(fnode.nodes)
                    body.edges.extend(fnode.edges)
                        
                    for port in fnode.out_ports:
                        edge=port.input_edge
                        port2=Port(body,port.type,port.index,port.label,False)
                        edge.attach_target(port2)
                    for port in c1.out_ports:
                        port2=Port(subs,port.type,port.index,port.label,False)
                        for edge in port.output_edges:
                            edge.attach_origin(port2)
                    #module.delete_node(fnode,False)
                    module.delete_node(c1,False)
                    
                    
                


def constant_folding_un (module: Module):
    for unode in module.get_nodes("Unary"):
        arg=unode.in_ports[0].input_node
        if type(arg) is Literal:
            result=operators[unode.operator](0,arg.value)
            result=unode.out_ports[0].type.convert(result)
            parent=unode.parent_node
            lit=module.Literal(result,unode.out_ports[0].type,parent)
            unode.out_ports[0].output_edges[0].attach_origin(lit.out_ports[0])
            module.delete_node(arg,True)
            module.delete_node(unode,True)
        elif unode.operator=='+':
            unode.out_ports[0].output_edges[0].attach_origin(arg.out_ports[0])
            module.delete_node(unode,True)
            
module=Module("subs.json")
open_substitution (module)

printm(module)

                  
                   
                     
