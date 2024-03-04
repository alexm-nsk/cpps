import sys

sys.path.append("..")

from ir.module import Module
from ir.edge import Edge
from ir.node import Node
from ir.ast_.literal import Literal
from ir.type import IntegerType, BooleanType

operators={
    '+': lambda x,y: x+y,
    '-': lambda x,y: x-y,
    '*': lambda x,y: x*y,
    '/': lambda x,y: x/y,
    '**': lambda x,y: x**y,
    '>': lambda x,y: x>y,
    '<': lambda x,y: x<y,
    '=': lambda x,y: x == y,
    '!=': lambda x,y: x != y,
    '>=': lambda x,y: x>=y,
    '<=': lambda x,y: x<=y
    }

def printm (module):
    import json
    
    print(json.dumps(module.save_to_json(), indent=2))
    
def constant_folding_bin (module: Module):
    for bnode in module.get_nodes("Binary"):
        left=bnode.in_ports[0].input_node
        right=bnode.in_ports[1].input_node
        if type(left) is Literal:
            if type(right) is Literal:
                result=operators[bnode.operator](left.value,right.value)
                result=bnode.out_ports[0].type.convert(result)
                parent=bnode.parent_node
                lit=module.Literal(result,bnode.out_ports[0].type,parent)
                bnode.out_ports[0].output_edges[0].attach_origin(lit.out_ports[0])
                module.delete_node(left,True)
                module.delete_node(right,True)
                module.delete_node(bnode,True)
    return module
  
def sub_bin_cut (module: Module):
    
    def reduce_to_arg (arg: Node, ind_opp, attach_to_opposite=True):
        #function removing the binary node and it's unnecessary argument
        nonlocal module
        nonlocal bnode
        edge=bnode.out_ports[0].output_edges[0]
        if attach_to_opposite:
            #if the non-literal value is unchanged by the operator (e.g. +0,*1)
            edge.attach_origin(bnode.in_ports[ind_opp].input_edge.from_)
            module.delete_node(arg,True)
        else:
            #if the result is always the same literal (e.g. *0)
            edge.attach_origin(arg.out_ports[0])
            opp=bnode.in_ports[ind_opp].input_node
            #disconnect the unneeded argument from binary
            edge2=bnode.in_ports[ind_opp].input_edge
            module.delete_edge(edge2)
            #check if the argument is variable given to container of bnode:
            if opp is not bnode.parent_node:
                #if the argument isn't variable (e.g. literal or function output), check if it's used somewhere else
                #if isn't remove
                #(it can and will create the unneeded code; removing that should be next to implement
                #might need revising: implicit connections?
                connect=False
                for port in opp.out_ports:
                if port.output_edges:
                    connect=True
                if not connect:
                    module.delete_node(opp,True)
        module.delete_node(bnode,True)
    
    
    
    for bnode in module.get_nodes("Binary"):
        #check for subexpressions that may be reduced
        #might need revise: is branching optimal?
        #using case might be more suitable here
        left=bnode.in_ports[0].input_node
        right=bnode.in_ports[1].input_node
        if type(left) is Literal:
            if left.value==0:
                if bnode.operator=='+':
                    reduce_to_arg(left,1)
                elif bnode.operator in ('*', '**', '/'):
                    reduce_to_arg(left,1,False)
                elif bnode.operator=='-':
                    un=module.Unary('-',bnode.out_ports[0].type,bnode.parent_node)
                    edge=bnode.out_ports[0].output_edges[0]
                    egde.attach_origin(un.out_ports[0])
                    edge=right.out_ports[0].output_edges[0]
                    edge.attach_target(un.in_ports[0])
                    module.delete_node(left,True)
                    module.delete_node(bnode,True)
            elif left.value==1:
                if bnode.operator=='*':
                    reduce_to_arg( left,1)
                elif bnode.operator=='**':
                    reduce_to_arg( left,1,False)
            elif left.value==True:
                if bnode.operator=='+':
                    reduce_to_arg( left,1,False)
                elif bnode.operator=='*':
                    reduce_to_arg( left,1)
            elif left.value==False:
                if bnode.operator=='*':
                    reduce_to_arg( left,1,False)
                elif bnode.operator=='+':
                    reduce_to_arg( left,1)
        elif type(right) is Literal:
            if right.value==0:
                if bnode.operator in ('+','-'):
                    reduce_to_arg( right,0)
                elif bnode.operator=='*':
                    reduce_to_arg( right,0,False)
                elif bnode.operator=='**':
                    lit=Literal(bnode.out_ports[0].type.convert(1),bnode.out_ports[0].type,bnode.parent_node)
                    edge=bnode.out_ports[0].output_edges[0]
                    egde.attach_origin(lit.out_ports[0])
                    module.delete_node(left,True)
                    module.delete_node(right,True)
                    module.delete_node(bnode,True)
            elif right.value==1:
                if bnode.operator in ('*','**','/'):
                    reduce_to_arg( right,0)
            elif right.value==True:
                if bnode.operator=='+':
                    reduce_to_arg( right,0,False)
                elif bnode.operator=='*':
                    reduce_to_arg( right,0)
            elif right.value==False:
                if bnode.operator=='*':
                    reduce_to_arg( right,0,False)
                elif bnode.operator=='+':
                    reduce_to_arg( right,0)
    return module


def constant_folding_if (module: Module):
    for ifnode in module.get_nodes("If"):
        cond=ifnode.condition.out_ports[0].input_node
        if type (cond) is Literal:
            if cond.value == True:
                module.swap_complex_node(ifnode.branches[0], ifnode)
                break
            else:
                if ifnode.branches[1]:
                    module.swap_complex_node(ifnode.branches[1], ifnode)
                    break
    return module
                
def constant_folding_let (module: Module):
    for letnode in module.get_nodes("Let"):
        body=letnode.body
        init=letnode.init
        for port in init.out_ports:
            #get the origin of a local variable and check if it's literal
            inp=port.input_node
            if type(inp) is Literal:
                lit=module.Literal(inp.value,port.type,body)
                #connect nodes using the unnecessary local variable to the literal
                #do the labels of the ports need to be deleted, if the variable they represent is?
                label=port.label
                for node in body.nodes:
                    if hasattr(node,'in_ports'):
                        for prt in node.in_ports:
                            if prt.label==label:
                                prt.input_edge.attach_origin(lit.out_ports[0])
                #remove the no longer needed literal
                module.delete_node(inp,true)
        #if all the local variables either were literals or are equivalent to the global ones, swap let with it's body 
        if not hasattr(init,'nodes'):
            module.swap_complex_node(body, letnode)
            
                        
                
            
    
    