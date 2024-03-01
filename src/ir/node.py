#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base class for IR nodes
"""
from .port import Port
from .type import get_type
from .edge import Edge
from copy import deepcopy

SUBNODE_NAMES = ["init", "body", "condition", "range_gen", "returns"]


def get_node(node_id):
    return Node.node_index[node_id]


class Node:
    needs_init = False

    def parse_ports(self, in_ports, out_ports):
        def parse_port(port, in_port):
            return Port(
                self.module.get_node(port["node_id"]),
                get_type(port["type"]),  # chooses an appropriate class
                port["index"],
                port["label"] if "label" in port else None,
                in_port,
                port["location"] if "location" in port else None,
            )

        if in_ports:
            self.in_ports = [parse_port(port, True) for port in in_ports]
        else:
            self.in_ports = []

        if out_ports:
            self.out_ports = [parse_port(port, False) for port in out_ports]
        else:
            self.out_ports = []

    @classmethod
    def load_from_data(cls, data, module):
        """Builds this node from data provided.
        Used when loading from JSON"""
        self = cls()
        self.module = module

        self.location = data["location"] if "location" in data else None
        self.id = data["id"]
        self.name = data["name"]

        if "dont_register" not in data or not data["dont_register"]:
            module.add_node(self)

        self.parse_ports(
            data["in_ports"] if "in_ports" in data else None,
            data["out_ports"] if "out_ports" in data else None,
        )

        if "nodes" in data:
                self.nodes = [
                    Node.class_map[node["name"]].load_from_data(node, module) for node in data["nodes"]
                ]

        if "branches" in data:
            self.branches = [
                Node.class_map["Branch"].load_from_data(br, module) for br in data["branches"]
            ]

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

            self.body = LetBody.load_from_data(data["body"], module)
            del data["body"]

        for field, value in data.items():
            if isinstance(value, dict):
                if "name" in value and value["name"] in self.class_map:
                    self.__dict__[field] = self.class_map[value["name"]].load_from_data(value, module)
            elif field in [
                "value",
                "operator",
                "function_name",
                "callee",
                "field",
                "pragmas",
                "pragma_group",
                "port_to_name_index",
            ]:
                self.__dict__[field] = value

        if "edges" in data:
            self.edges = []
            self.module.parse_edges(data["edges"], self)

        self.post_init()

        return self

    def post_init(self):
        pass

    def ir_(self) -> dict:
        """Common for all nodes, converts the fields to export-ready dict"""
        retval = deepcopy(self).__dict__
        del retval["module"]
        for key in ["in_ports", "out_ports", "nodes", "edges"]:
            if key in retval:
                retval[key] = [item.ir_() for item in retval[key]]
        for key in ["init", "body", "range_gen", "returns", "condition"]:
            if key in retval:
                retval[key] = retval[key].ir_()
        if hasattr(self, "branches"):
            retval["branches"] = [branch.ir_() for branch in retval["branches"]]
        if "pragmas" in retval and retval["pragmas"] == []:
            del retval["pragmas"]
        return retval

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

    def is_parent(self, compared_node):
        """Returns True if this node is contained in compared_node's
        internal nodes, otherwise returns False"""
        if self == compared_node:
            return True
        if "nodes" not in compared_node.__dict__:
            return False
        if self in compared_node.nodes:
            return True
        return False

    def trace_back(self):
        """Finds all chains (nodes and edges) leading to this node's inputs.
        Returns the Nodes and all involved Edges.
        """
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

    def get_node_paragma_group(node):
        if not hasattr(node, "pragma_group"):
            return [node]

        return [
            n
            for _, n in Node.node_index.items()
            if hasattr(n, "pragma_group") and n.pragma_group == node.pragma_group
        ]

    def get_group(group_index):
        return [
            node
            for _, node in Node.node_index.items()
            if hasattr(node, "pragma_group") and node.pragma_group == group_index
        ]

    @property
    def parent_node(self):
        for name, node in self.module.nodes.items():
            if hasattr(node, "nodes") and self in node.nodes:
                return node

            if hasattr(node, "branches"):
                for br in node.branches:
                    if hasattr(br, "nodes") and self in br.nodes:
                        return br

            for sub_node in SUBNODE_NAMES:
                if (
                    hasattr(node, sub_node)
                    and hasattr(node.__dict__[sub_node], "nodes")
                    and self in node.__dict__[sub_node].nodes
                ):
                    return node.__dict__[sub_node]

        return None

    def get_containing_function(self):
        """returns the function that contains this node"""
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

    def has_nodes(self):
        if hasattr(self, "nodes"):
            return len(self.nodes) > 0
        return False

    @property
    def is_complex(self):
        if hasattr(self, "nodes"):
            return True

        return False

    @property
    def is_multi(self):
        '''determines if this node has unattached inner nodes
        (like if, let, or loop)'''
        if hasattr(self, "branches"):
            return True
        for subnode in SUBNODE_NAMES:
            if hasattr(self, subnode):
                return True
        return False

    @property
    def is_basic(self):
        if not self.is_complex and not self.is_multi:
            return True
        return False

    @property
    def is_cluster(self):
        return self.name in ["Then",
                             "ElseIf",
                             "Else",
                             "Condition",
                             "Body",
                             "RangeGen",
                             "Init",
                             "Returns"]

    @property
    def num_subnodes(self):
        '''returns number of all nodes recursively contained in this node
        not memoized yet, because the graph may change and that would require additional handling'''
        num_nodes = 0
        if hasattr(self, "nodes"):
            num_nodes += len(self.nodes) + sum([n.num_subnodes for n in self.nodes])

        if hasattr(self, "branches"):
            num_nodes += len(self.branches) + sum([n.num_subnodes for n in self.branches])

        for subnode in SUBNODE_NAMES:
            if hasattr(self, subnode):
                num_nodes += 1 + self.__dict__[subnode].num_subnodes

        return num_nodes

    def get_clusters(self):

        if hasattr(self, "nodes"):
            return []

        clusters = []

        if hasattr(self, "branches"):
            clusters += [cl for cl in self.branches]

        for subnode in SUBNODE_NAMES:
            if hasattr(self, subnode):
                clusters += [self.__dict__[subnode]]

        return clusters

