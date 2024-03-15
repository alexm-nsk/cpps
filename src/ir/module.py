"""represents Cloud Sisal module"""

from .parse_ir import parse_node
import json
from utils.python_names import python_names, json_names
from .edge import Edge
from .node import Node, SUBNODE_NAMES
from .type import get_type
from .port import Port
from .ast_ import alg, literal, let, common
from .error import IRProcessingError
from copy import deepcopy

PORT_MISMATCH_TEXT = "configuration mismatch when swapping nodes."


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
        if node_to_delete.id in self.nodes:
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
                if hasattr(subnode, "nodes"):
                    for n in subnode.nodes:
                        self.__delete_node__(n, True, False)
                self.__delete_node__(subnode, False, False)
        # delete branches from Ifs:
        if hasattr(node, "branches"):
            for branch in node.branches:
                if hasattr(branch, "nodes"):
                    for n in branch.nodes:
                        self.__delete_node__(n, True, False)
                self.__delete_node__(branch, False, False)

        self.__delete_node__(node, delete_attached_edges, not node.is_cluster)

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

    @staticmethod
    def check_ports_compatibility(src_node, dst_node):
        """test if port configurations (numbers of input and
        output ports and their types) match"""
        # TODO add compatible types and conversion nodes
        if len(src_node.in_ports) != len(dst_node.in_ports):
            raise IRProcessingError(
                "Input port" + PORT_MISMATCH_TEXT,
                (f"Trying to swap {src_node} with {dst_node}."),
            )

        # test if port configurations match:
        if len(src_node.out_ports) != len(dst_node.out_ports):
            raise IRProcessingError(
                "Output port" + PORT_MISMATCH_TEXT,
                (f"Trying to swap {src_node} with {dst_node}."),
            )

        for src_ip, dst_ip in zip(src_node.in_ports, dst_node.in_ports):
            if type(src_ip.type) != type(dst_ip.type):
                raise IRProcessingError(
                    "Input port type " + PORT_MISMATCH_TEXT,
                    (
                        f"Trying to swap {src_node} with {dst_node}."
                        f"Input port {src_ip.index}({src_ip.type}) vs."
                        f"Input port {dst_ip.index}({dst_ip.type})"
                    ),
                )

        for src_op, dst_op in zip(src_node.out_ports, dst_node.out_ports):
            if type(src_op.type) != type(dst_op.type):
                raise IRProcessingError(
                    "Input port type " + PORT_MISMATCH_TEXT,
                    (
                        f"Trying to swap {src_node} with {dst_node}."
                        f"Output port {src_op.index}({src_op.type}) vs."
                        f"Output port {dst_op.index}({dst_op.type})"
                    ),
                )

    def swap_complex_node(self, src_node, dst_node):
        """replaces dst_node with src_node making all necessary
        connections, will only work with clusters (like cond, branch, etc.)"""

        self.check_ports_compatibility(src_node, dst_node)

        # node containing dst_node:
        parent = dst_node.parent_node

        # reconnect the inputs:
        for d_i_p, s_i_p in zip(dst_node.in_ports, src_node.in_ports):
            # ports connected to src_node in_ports
            # (the ones that are first at the input
            # and directly connected to it)
            for border_port in s_i_p.connected_ports:
                border_port.input_edge.attach_origin(d_i_p.input_port)
            self.delete_edge(d_i_p.input_edge)

        # reconnect the outputs:
        for d_o_p, s_o_p in zip(dst_node.out_ports, src_node.out_ports):
            for out_port in d_o_p.connected_ports:
                out_port.input_edge.attach_origin(s_o_p.input_port)
            self.delete_edge(s_o_p.input_edge)

        for edge in src_node.edges:
            edge.containing_node = parent
        parent.edges += src_node.edges

        if src_node.has_nodes():
            parent.nodes += src_node.nodes

        src_node.edges = []
        src_node.nodes = []

        # parent.nodes.append(src_node)
        self.delete_node(dst_node, delete_attached_edges=False)
        self.delete_node(src_node, delete_attached_edges=False)

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
        bin.id = self.get_new_node_id()
        bin.operator = operator
        bin.in_ports = [
            Port(bin, left_type, 0, "left operand", True, ""),
            Port(bin, right_type, 1, "right operand", True, ""),
        ]
        # TODO use typemap
        bin.out_ports = [Port(bin, left_type, 0, "output", False, "")]
        self.add_node(bin)
        container.nodes.append(bin)
        bin.module = self
        return bin

    def Unary(self, operator, value_type, container):
        un = alg.Unary()
        un.id = self.get_new_node_id()
        un.operator = operator
        un.in_ports = [Port(un, value_type, 0, "input", True, "")]
        # TODO also use typemap
        un.out_ports = [Port(un, value_type, 0, "output", False, "")]
        self.add_node(un)
        container.nodes.append(un)
        un.module = self
        return un

    def Let(
        self,
        container,
        variables=None,
        output_values=None,
        copy_in_ports_from_container=True,
    ):
        """input_values, output_values and variables are lists of tuples
        like [(name, type), (name, type)...]."""
        let_node = let.Let()
        let_node.id = self.get_new_node_id()
        let_node.module = self
        container.nodes.append(let_node)

        body = let_node.body = let.Body()
        init = let_node.init = common.Init()
        body.module = self
        init.module = self
        init.id = self.get_new_node_id()
        body.id = self.get_new_node_id()

        if copy_in_ports_from_container:
            num_in_ports = len(container.in_ports)
        else:
            num_in_ports = 0

        def make_ports(node, values, in_ports):
            container_ports = []
            if in_ports and copy_in_ports_from_container:
                for index, cont_port in enumerate(container.in_ports):
                    let_port = deepcopy(cont_port)
                    let_port.node = node
                    container_ports.append(let_port)

            custom_ports = [
                Port(node, type_, index, label, in_ports, "")
                for index, (label, type_) in enumerate(
                    values, num_in_ports if in_ports else 0
                )
            ]
            return container_ports + custom_ports

        let_node.in_ports = make_ports(let_node, [], True)
        let_node.out_ports = make_ports(let_node, output_values, False)

        init.in_ports = make_ports(init, [], True)
        init.out_ports = make_ports(init, variables, False)

        body.in_ports = make_ports(body, variables, True)
        body.out_ports = make_ports(body, output_values, False)

        return let_node

    def move_subgraph(self, src_nodes: list, src_edges: list, dst_node):
        pass
