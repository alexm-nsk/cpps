"""represents Cloud Sisal module"""

from .parse_ir import parse_node
import json
from utils.python_names import python_names, json_names
from .edge import Edge
from .node import Node, SUBNODE_NAMES
from .type import get_type
from .port import Port
from .ast_ import alg, literal


class Module:
    def reset(self):
        self.definitions = {}
        self.functions = {}
        self.nodes = {}
        self.ports = {}
        self.edges = []
        self.edges_from = {}
        self.edge_to = {}
        self.deleted_nodes = []

    def __init__(self, file_name=None):
        self.reset()
        if file_name:
            self.load_from_json(file_name)

    def add_node(self, node):
        self.nodes[node.id] = node

    def get_node(self, node_id):
        """Returns node specified by it's ID"""
        return self.nodes[node_id]

    def get_nodes(self, type_):
        """Returns a list of nodes of thr specified type"""
        return [node for name, node in self.nodes.items() if node.name == type_]

    def delete_edge(self, edge):
        """Deletes the edge from this module"""
        from_port = edge.from_
        to_port = edge.to
        # remove edge from all registries:
        self.edges.remove(edge)
        if from_port.id in self.edges_from:
            del self.edges_from[from_port.id]
        if to_port.id in self.edge_to:
            del self.edge_to[to_port.id]
        edge.containing_node.edges.remove(edge)

    def delete_edges_attached_to_node(self, node):
        """Deletes edges connected to node's output ports or it's input ports"""
        if hasattr(node, "in_ports"):
            for i_p in node.in_ports:
                if i_p.id in self.edge_to:
                    self.delete_edge(self.edge_to[i_p.id])
        if hasattr(node, "out_ports"):
            for o_p in node.out_ports:
                edges_to_delete = [
                    edge_to_delete for edge_to_delete in self.edges_from[o_p.id]
                ]
                for edge in edges_to_delete:
                    self.delete_edge(edge)

    def __delete_node__(self, node, delete_attached_edges, del_from_parent):
        """Used by delete_node, don't call from outside of Module class"""
        node_to_delete = self.nodes[node] if node is str else node
        if del_from_parent:
            parent_node = node.parent_node
            parent_node.nodes.remove(self.nodes[node.id])

        if delete_attached_edges:
            self.delete_edges_attached_to_node(node)

        if hasattr(node, "edges"):
            for edge in node.edges:
                # properly remove all edges contained in this node
                # from the module
                self.delete_edge(edge)

        self.deleted_nodes.append(node_to_delete.id)
        del self.nodes[node_to_delete.id]

    def delete_node(self, node: Node, delete_attached_edges=False):
        """Deletes a node from this module.
        delete_attached_edges determines if all attached edges
        should also be removed"""
        # delete subnodes contained in "nodes":
        if hasattr(node, "nodes"):
            for n in node.nodes:
                self.__delete_node__(n, True, False)
        # delete unattached subnodes like Init, Body, etc.:
        for subnode_name in SUBNODE_NAMES:
            if hasattr(node, subnode_name):
                subnode = node.__dict__[subnode_name]
                for n in subnode.nodes:
                    self.__delete_node__(n, True, False)
                self.__delete_node__(subnode, True, False)
        # delete branches from Ifs:
        if hasattr(node, "branches"):
            for branch in node.branches:
                for n in branch.nodes:
                    self.__delete_node__(n, True, False)
                self.__delete_node__(branch, True, False)

        self.__delete_node__(node, delete_attached_edges, True)

    def load_from_json(self, file_name):
        """Loads module from JSON file"""
        file_data = open(file_name, "r").read()
        self.load_from_json_data(json.loads(file_data))

    def load_from_json_data(self, module_json_data):
        """Loads module from JSON data in RAM"""
        self.reset()
        module_data = python_names(module_json_data)
        for fn_ in module_data["functions"]:
            function = parse_node(fn_, self)
            self.functions[function.function_name] = function

        if "definitions" in module_data:
            for def_ in module_data["definitions"]:
                self.definitions[def_["name"]] = get_type(def_["type"])

    def save_to_json(self):
        """Creates a dictionary suitable for JSON export out of this module
        it changes names to camelCase to fit JS convention
        """
        output = {
            "functions": [function.ir_() for name, function in self.functions.items()],
            "definitions": [
                definition.ir_() for _, definition in self.definitions.items()
            ],
        }
        return json_names(output)

    def parse_edges(self, edges, node):
        """Used for reading edges from JSON representation, no need to call it outside of the class"""
        new_edges = []
        for edge in edges:
            if "from" in edge and "to" in edge:
                src_index = edge["from"][1]
                dst_index = edge["to"][1]

                src_node = self.get_node(edge["from"][0])
                dst_node = self.get_node(edge["to"][0])

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node.__dict__[from_type + "_ports"][src_index]
                to = dst_node.__dict__[to_type + "_ports"][dst_index]

            else:
                # sisal-cl IRs:
                src_index = edge[0]["index"]
                dst_index = edge[1]["index"]

                src_node = self.get_node(edge[0]["node_id"])
                dst_node = self.get_node(edge[1]["node_id"])

                from_type = "in" if dst_node.is_parent(src_node) else "out"
                to_type = "out" if src_node.is_parent(dst_node) else "in"

                from_ = src_node.__dict__[from_type + "_ports"][src_index]
                to = dst_node.__dict__[to_type + "_ports"][dst_index]

            Edge(from_, to, node)

    def get_new_node_id(self):
        """Get an id for a new node: it will use free names from previously
        deleted nodes, or create a new one"""
        if self.deleted_nodes:
            return self.deleted_nodes.pop(0)
        return "node" + str(len(self.nodes))

    def Literal(self, value, type, container: Node):
        """Create a new literal node and put it inside the "container" node"""
        lit = literal.Literal()
        lit.value = value
        lit.out_ports = [Port(lit, type, 0, "value", False, "")]
        lit.id = self.get_new_node_id()
        self.add_node(lit)
        lit.module = self
        container.nodes.append(lit)
        lit.name = "Literal"
        return lit

    def Binary(self, operator, left_type, right_type, container):
        bin = alg.Binary()
        bin.operator = operator
        bin.in_ports = [Port(bin, left_type, 0, "left operand", True, ""),
                        Port(bin, right_type, 1, "right operand", True, "")]
        #TODO use typemap
        bin.out_ports = [Port(bin, left_type, 0, "output", False, "")]
        self.add_node(bin)
        container.nodes.append(bin)
        bin.module = self
        return bin
