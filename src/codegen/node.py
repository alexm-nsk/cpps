#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator node (mostly deserealizing code)
"""
from .port import Port
from .type import get_type
from .edge import Edge
from .cpp.cpp_codegen import cpp_eval


def get_node(node_id):
    return Node.node_index[node_id]


def to_cpp_method(fn):
    def wrapped(self, block):
        if (hasattr(self, "name_child_output_values") and
           self.name_child_output_values):

            # label the ports:
            for index, o_p in enumerate(self.out_ports):
                src_port = Edge.edge_to[o_p.id].from_
                if src_port.node.name != "Lambda":
                    src_port.label = (self.result_name +
                                  (str(index) if len(self.out_ports) > 1
                                   else ""))

            for o_p in self.out_ports:
                if not o_p.label:
                    if not hasattr(self, "name"):
                        o_p.label = self.name + str(o_p.index)
                    else:
                        o_p.label = self.__class__.__name__ + str(o_p.index)

        if (
            hasattr(self, "copy_parent_input_values")
            and self.copy_parent_input_values
        ):
            for i_p in self.in_ports:
                cpp_eval(i_p, block)

        return fn(self, block)

    return wrapped


class Node:

    node_index = {}
    needs_init = False

    def name_child_ports(self):
        # label child nodes' output ports:
        for o_p in self.out_ports:
            src_port = Edge.edge_to[o_p.id].from_
            # make sure it's not input value
            # which must be determined by now:
            if not src_port.in_port:
                src_port.label = o_p.label
                # mark port as renamed, so it can pick
                # appropriate name for it's variable:
                src_port.renamed = True

    @staticmethod
    def get_node(node_id):
        return Node.node_index[node_id]

    def get_node_paragma_group(node):
        if not hasattr(node, "pragma_group"):
            return [node]

        return [n for _, n in Node.node_index.items()
                if hasattr(n, "pragma_group")
                and n.pragma_group == node.pragma_group]

    def get_group(group_index):
        return [node for _, node in Node.node_index.items()
                if hasattr(node, "pragma_group")
                and node.pragma_group == group_index]

    def get_parent_node(self):
        for name, node in Node.node_index.items():
            if hasattr(node, "nodes") and self in node.nodes:
                return node

            if hasattr(node, "branches"):
                for br in node.branches:
                    if hasattr(br, "nodes") and self in br.nodes:
                        return br

            for sub_node in ["init", "body", "condition", "range_gen", "returns"]:
                if (hasattr(node, sub_node) and
                   hasattr(node.__dict__[sub_node], "nodes") and
                   self in node.__dict__[sub_node].nodes):
                    return sub_node

        return None

    def get_containing_function(self):
        parent = self.get_parent_node()
        while True:
            new_parent = parent.get_parent_node()
            if not new_parent:
                if parent.name == "Lambda":
                    return parent
                else:
                    raise Exception("IR error: top node isn't a function.")
            else:
                parent = new_parent

    @staticmethod
    def parse_port(port, in_port):
        return Port(
            Node.get_node(port["node_id"]),
            get_type(port["type"]),  # chooses an appropriate class
            port["index"],
            port["label"] if "label" in port else None,
            in_port
        )

    def parse_ports(self, in_ports, out_ports):
        if in_ports:
            self.in_ports = [self.parse_port(port, in_port=True)
                             for port in in_ports]
        else:
            self.in_ports = []

        if out_ports:
            self.out_ports = [self.parse_port(port, in_port=False)
                              for port in out_ports]
        else:
            self.out_ports = []

    def is_parent(self, compared_node):
        if self == compared_node:
            return True
        if "nodes" not in compared_node.__dict__:
            return False
        if self in compared_node.nodes:
            return True
        return False

    def parse_edges(self, edges):
        self.edges = []
        for edge in edges:
            if "from" in edge and "to" in edge:
                src_index = edge["from"][1]
                dst_index = edge["to"][1]

                src_node = self.node_index[edge["from"][0]]
                dst_node = self.node_index[edge["to"][0]]

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node.__dict__[from_type + "_ports"][src_index]
                to = dst_node.__dict__[to_type + "_ports"][dst_index]

            else:
                # sisal-cl IRs:
                src_index = edge[0]["index"]
                dst_index = edge[1]["index"]

                src_node = self.node_index[edge[0]["node_id"]]
                dst_node = self.node_index[edge[1]["node_id"]]

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node.__dict__[from_type + "_ports"][src_index]
                to = dst_node.__dict__[to_type + "_ports"][dst_index]

            self.edges.append(Edge(from_, to))

    def get_pragma(self, name):
        if hasattr(self, "pragmas"):
            for p in self.pragmas:
                if p["name"] == name:
                    return p
        return None

    def remove_pragma(self, name):
        if hasattr(self, "pragmas"):
            for p in self.pragmas:
                if p["name"] == name:
                    self.pragmas.remove(p)
        return None

    def read_data(self, data):
        if "dont_register" not in data or not data["dont_register"]:
            Node.node_index[data["id"]] = self
        self.location = data["location"] if "location" in data else None
        self.id = data["id"]
        self.name = data["name"]
        self.parse_ports(
            data["in_ports"] if "in_ports" in data else None,
            data["out_ports"] if "out_ports" in data else None,
        )

        if "nodes" in data:
            self.nodes = [Node.class_map[node["name"]](node)
                          for node in data["nodes"]]

        if "branches" in data:
            self.branches = [Node.class_map["Branch"](br)
                             for br in data["branches"]]

        # sisal-cl IRs only:
        if "results" in data:
            for index, result in enumerate(data["results"]):
                self.out_ports[index].label = result[0]

        # sisal-cl IRs only:
        if "params" in data:
            for index, result in enumerate(data["params"]):
                self.in_ports[index].label = result[0]

        if self.name == "Let":
            from .ast_.let import LetBody

            self.body = LetBody(data["body"])
            del data["body"]

        for field, value in data.items():
            if isinstance(value, dict):
                if "name" in value and value["name"] in self.class_map:
                    self.__dict__[field] = self.class_map[value["name"]](value)
            elif field in ["value", "operator", "function_name",
                           "callee", "field", "pragmas", "pragma_group", "port_to_name_index"]:
                self.__dict__[field] = value

        if "edges" in data:
            self.parse_edges(data["edges"])

    def __new__(cls, data):
        return object.__new__(cls)

    def __init__(self, data):
        self.read_data(data)

    def trace_back(self):
        '''Finds all chains (nodes and edges) leading to this node's inputs.
           Returns the Nodes and all involved Edges.
        '''
        internal_edges = []
        input_edges = []
        nodes = [self]

        for i_p in self.in_ports:
            input_edge = Edge.edge_to[i_p.id]
            from_ = input_edge.from_
            if not from_.in_port:
                new_nodes, new_edges, new_input_edges = from_.node.trace_back()
                nodes.extend(new_nodes)
                internal_edges.extend(new_edges)
                input_edges.extend(new_input_edges)
                internal_edges.append(input_edge)
            else:
                input_edges.append(input_edge)

        return nodes, internal_edges, input_edges
