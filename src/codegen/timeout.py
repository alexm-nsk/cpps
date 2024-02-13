'''Process timeout pragma in internal (non-function) nodes
Turns expressions into functions and calls'''
from .node import Node
from .edge import Edge
from .ast_.function import Function
from .ast_.call import FunctionCall
from .port import Port
from collections import OrderedDict


def collect_pragma_ir(node):
    '''collect all nodes involved in calculations affected
    by the pragma'''
    nodes, internal_edges, input_edges, output_edges = [], [], [], []

    group = Node.get_node_paragma_group(node)

    for n in group:
        new_nodes, new_internal_edges, new_input_edges = n.trace_back()
        nodes += new_nodes
        internal_edges += new_internal_edges
        input_edges += new_input_edges

    for n in group:
        for o_p in n.out_ports:
            output_edges.extend(Edge.edges_from[o_p.id])

    return nodes, internal_edges, input_edges, output_edges


def process_timeout():
    '''Move expressions affected by a timeout pragma into a new service
       function (that is marked with the same pragma) and replace them with
       a call. Timed function execution is implemented in
       codegen/ast_/function.py. This is done at IR level'''

    for id_, node in Node.node_index.copy().items():
        if node.name != "Lambda" and node.get_pragma("timeout"):
            # nodes - all the nodes involved in calculation
            # internal edges - all the edges between those nodes
            # input edges - all the edges pointing to nodes from the outside
            # output_edges - edges that point from the nodes to the outside
            parent_node = node.get_parent_node()

            (nodes, internal_edges,
                input_edges, output_edges) = collect_pragma_ir(node)

            # create a new function for the calculation of the
            # pragma-affected expression
            new_function = Function(dict(
                                    id="node" + str(len(Node.node_index)),
                                    function_name=Function.get_service_name
                                    ("timed_expression"),
                                    name="Lambda",
                                    edges=[], nodes=[],
                                    pragmas=node.pragmas.copy()))

            new_call = FunctionCall(dict(
                                    callee=new_function.function_name,
                                    id="node" + str(len(Node.node_index)),
                                    name="FunctionCall"))

            for index, e in enumerate(output_edges):
                label = "result" + str(index)
                func_out_port = Port(new_function, e.from_.type,
                                     index, label, False)
                call_out_port = Port(new_call, e.from_.type,
                                     index, label, False)
                new_function.out_ports.append(func_out_port)
                new_call.out_ports.append(call_out_port)

                service_func_output_edge = Edge(
                                            e.from_,
                                            new_function.out_ports[index])
                new_function.edges.append(service_func_output_edge)
                e.attach_origin(new_call.out_ports[index])

            # collect ports from edges "froms",
            # save edges connected to each in a list assigned to the port
            # store them in an OrderedDict
            edges_from_port = OrderedDict()
            for edge_index, e in enumerate(input_edges):
                if e.from_.id not in edges_from_port:
                    edges_from_port[e.from_.id] = [e]
                    port_index = len(edges_from_port)
                    label = "arg_" + str(port_index)
                    function_in_port = Port(new_function, e.to.type,
                                            port_index, e.from_.label, True)
                    call_in_port = Port(new_call, e.to.type,
                                        port_index, label, True)
                    new_function.in_ports.append(function_in_port)
                    new_call.in_ports.append(call_in_port)
                else:
                    edges_from_port[e.from_.id].append(e)

            # use the ordered dict to reassign edges' targets
            # and create new corresponding edges in the service function
            for index, (_, edges) in enumerate(edges_from_port.items()):
                for e in edges:
                    target_port = e.to
                    e.attach_target(new_call.in_ports[index])
                    service_func_input_edge = Edge(
                                            new_function.in_ports[index],
                                            target_port)
                    new_function.edges.append(service_func_input_edge)

            # remove the timeout from all the involved nodes
            for n in nodes:
                n.remove_pragma("timeout")
                # move nodes into the service function
                new_function.nodes.append(n)
                parent_node.nodes.remove(n)

            parent_node.nodes.append(new_call)

            # move input edges to the service function
            for index, e in enumerate(internal_edges):
                new_function.edges.append(e)
                parent_node.edges.remove(e)
