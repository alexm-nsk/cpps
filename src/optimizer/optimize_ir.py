import sys

sys.path.append("/home/newt/cpps/src")


from ir.module import Module
from ir.edge import Edge
from ir.node import Node
from ir.ast_.literal import Literal
from ir.ast_.call import FunctionCall
from ir.ast_.function import Function
from ir.type import IntegerType, BooleanType
from ir.port import Port
import configparser

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


def constant_folding_bin(module, bnode: Node):
        left = bnode.in_ports[0].input_node
        right = bnode.in_ports[1].input_node
        if type(left) is Literal:
            if type(right) is Literal:
                if ((left.value!='Error')and(right.value!='Error')):#or ErrDef(bnode) - как реализовать ErrDef?
                    result = operators[bnode.operator](left.value, right.value)
                    result = bnode.out_ports[0].type.convert(result)
                    parent = bnode.parent_node
                    lit = module.Literal(result, bnode.out_ports[0].type, parent)
                    bnode.out_ports[0].output_edges[0].attach_origin(lit.out_ports[0])
                    module.delete_node(left, True)
                    module.delete_node(right, True)
                    module.delete_node(bnode, True)
        return module

def sub_bin_cut(module, bnode: Node):
    
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
        else:
            # if the result is always the same literal (e.g. *0)
            edge.attach_origin(arg.out_ports[0])            
        module.delete_node(bnode, True)

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
                edge.attach_origin(un.out_ports[0])
                edge = bnode.in_ports[1].input_edge
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
                edge.attach_origin(lit.out_ports[0])
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

def constant_folding_if(module, ifnode: Node):
    cond = ifnode.condition.out_ports[0].input_node
    if type(cond) is Literal:
        if cond.value == True:
            module.swap_complex_node(ifnode.branches[0], ifnode)
        else:
            if ifnode.branches[1]:
                module.swap_complex_node(ifnode.branches[1], ifnode)
    return module

def constant_folding_let(module, letnode: Node):
    body = letnode.body
    init = letnode.init
    for port in init.out_ports:
        # get the origin of a local variable and check if it's literal
        inp = port.input_node
        if type(inp) is Literal:
            # connect nodes using the unnecessary local variable to the literal
            # do the labels of the ports need to be deleted, if the variable they represent is?
            lb = port.label
            bports=body.get_in_ports_by_label(lb)
            for port2 in bports:
                edges=port2.output_edges
                for edge in edges:
                    lit = module.Literal(inp.value, port.type, body)
                    edge.attach_origin(lit.out_ports[0])
                body.delete_port(port2)
            # remove the no longer needed literal
            module.delete_node(inp, True)
    # if all the local variables either were literals or are equivalent to the global ones, swap let with it's body
    if not init.nodes:
        module.swap_complex_node(body,letnode)
    return module

def open_substitution(module, callnode: Node): #тут надо будет перепилить с учетом списков вызовов
    f = callnode.callee
    if f != "main":
        i = 0
        for c in module.get_nodes("FunctionCall"):
            if c.callee == f:
                c1 = c
                i += 1
        if i == 1:
            fnode=False
            for fn in module.get_nodes('Lambda'):
                if fn.function_name==f:
                    fnode=fn
            if not fnode:
                raise Exception("Nonexistent function is called")
            parent=c1.get_containing_function
            if parent is not fnode:
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
                cnodes.remove(c1)
                init.nodes.extend(cnodes)
                init.edges.extend(internal_edges)
                if parent.in_ports:
                    for port1,port2,port3 in zip(parent.in_ports, init.in_ports, subs.in_ports):
                        for edge in port1.output_edges:
                            if edge in input_edges:
                                tar=edge.to
                                edge.attach_target(port3)
                                edge2=Edge(port2,tar,init)
                                
                if c1.in_ports:
                    for port1, port2 in zip(fnode.in_ports, body.in_ports):
                        for edge in port1.output_edges:
                            edge.attach_origin(port2)
                            
                    for port1,port2 in zip(c1.in_ports,init.out_ports):
                        edge=port1.input_edge
                        edge.attach_target(port2)
                        
                body.nodes+=fnode.nodes
                for edge in fnode.edges:
                    edge.containing_node=body
                    body.edges.append(edge)
                    
                for port1,port2 in zip(fnode.out_ports,body.out_ports):
                    edge=port1.input_edge
                    edge.attach_target(port2)
                  
                for port1,port2 in zip(c1.out_ports,subs.out_ports):
                    for edge in port1.output_edges:
                        edge.attach_origin(port2)
                module.add_node(subs)
                del fnode.nodes
                del fnode.edges
                module.delete_node(fnode)
                module.delete_node(c1)
                module.add_node(subs.init)
                module.add_node(subs.body)
                module.edges.extend(internal_edges)
                module.edges.extend(subs.body.edges)
    return module

def constant_folding_un (module, unode: Node):
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
    return module
        
def bin_red (module, bnode: Node):
    constant_folding_bin(module, bnode)
    sub_bin_cut(module, bnode)
    return module
        
reductions = {'Binary': lambda x,y:  bin_red(x,y),
    'Unary': lambda x,y:  constant_folding_un(x,y),
    'FunctionCall': lambda x,y:  open_substitution(x,y),
    'If':lambda x,y:  constant_folding_if(x,y),
    'Let':lambda x,y:  constant_folding_let(x,y)
    }

red_names={'Binary','Unary','FunctionCall','If','Let'}          
 
def parseRanks (complex_node: Node):
    rankMap={}
    def tracebackMap(node:Node):
        nonlocal rankMap
        nonlocal complex_node
        acc_set=set()
        if hasattr(node,"in_ports"):
            for port in node.in_ports:
                new_node=port.input_node
                if not new_node==complex_node:
                    acc_set.union(tracebackMap(new_node))
                    acc_set.add(new_node)
        r=len(acc_set)
        rankMap[node]=[r, acc_set]
        return acc_set

    for port in complex_node.out_ports:
        tracebackMap (port.input_node)
    return rankMap

def right_numeration (rankMap):
    r_max=0
    for m in rankMap.values():
        if m[0]>r_max:
            r_max=m[0]
    r=0
    nums={}
    k=1
    while r<=r_max:
        for node in rankMap:
            if (r==rankMap[node][0])and(node not in nums.values()):
                nums[k]=node
                k+=1
        r+=1
    return nums

def unused_clean (module, complex_node: Node):
    rankMap=parseRanks(complex_node)
    nodes_at_work=set()
    for acc in rankMap.values():
        nodes_at_work.union(acc[1])
    for node in complex_node.nodes:
        if node.id not in nodes_at_work:
            module.delete_node(node,True)
    return module

def IR_traverse (module, complex_node):
    #module=unused_clean(module,complex_node)
    clean_nodes=set()
    ind=1
    while ind==1:
        rankMap=parseRanks(complex_node)
        nums=right_numeration(rankMap) #сделать, если получится, так, чтобы преобразования сами пересчитывали нумерацию и ранги. вряд ли выйдет, как будто
        ind=0
        for i in range (1,len(nums)+1):
            node=nums[i]
            if (rankMap[node][1].issubset(clean_nodes))and(node not in clean_nodes):
                ind=1
                name=node.name
                if node.is_complex:
                    module=IR_traverse(module,node)
                    break
                if node.is_multi:
                    if name=="Let":
                        module=IR_traverse(module,node.init)
                        module=IR_traverse(module,node.body)
                    elif name=="If":
                        module=IR_traverse(module,node.condition)
                    elif name=="Case":
                        pass
                clean_nodes.add(node)
                if name in red_names:
                    module=reductions[name](module,node)#не забыть учесть преобразования внутренних узлов, карту переменных (а они не только в let?...)
                    break
    #module=unused_clean(module,complex_node)
    return module
    
def default (module: Module):
    functions=module.get_nodes('Lambda')
    for f in functions:
        if f.function_name=='main':
            sismain=f #можно ли в этот просмотр запихать что-нибудь еще? можно ли изящнее
    module=IR_traverse(module,sismain)
    return module

def optimize_ir (module):
    config = configparser.ConfigParser()  # создаём объект парсера
    settings=config.read("optimizer_settings.ini")
    if settings['BASIC SETTINGS']['mode']=='default':
        module=default(module)
    return module
