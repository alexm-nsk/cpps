#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""C++ code generation"""
from ..edge import Edge

GROUP_VARIABLES = True

CPP_INDENT = "  "
CPP_MODULE_HEADER = """\
#include <stdio.h>
#include <vector>
#include <iostream>
#include <fstream>
#include <json/json.h>// uses jsoncpp library

using namespace std;

template <typename Iterable>

Json::Value iterable_to_json(Iterable const& cont) {
    Json::Value v;
    for (auto&& element: cont) {
        v.append(element);
    }
    return v;
}

template <typename I>
vector<I> operator || (const vector<I>& lhs, const vector<I>& rhs){
    vector<I> result = lhs;
    result.insert(result.end(), rhs.begin(), rhs.end());
    return result;
}

inline int size (vector<int> A)
{
    return A.size();
}

//------------------------------------------------------------


"""


def indent_cpp(src_code, indent_level=1):
    indent = indent_level * CPP_INDENT
    return indent + src_code.replace("\n", "\n" + indent)


class CppVariable:

    variable_index = {}

    def __init__(self, name, type_, value=None):
        self.type_ = type_
        self.name = name
        if name not in self.variable_index:
            self.variable_index[name] = 0
        self.variable_index[name] += 1

        if self.variable_index[name] > 1:
            self.name = name + str(self.variable_index[name])

        self.value = value

    def __repr__(self):
        return f"CppVariable<{self.name}, {self.type_}, {self.value}>"

    def __str__(self):
        return self.name

    def definition_str(self):
        return f"{self.type_.cpp_type} {self.name}"


class CppModule:
    def __init__(self, name: str, functions: dict, definitions: list = []):
        self.functions = []
        for name, f in functions.items():
            self.functions += [f.to_cpp()]

        from ..ast_.function import create_main

        self.functions += [create_main()]

    def __str__(self):
        return CPP_MODULE_HEADER + "\n\n".join(self.functions)


class CppExpression:
    def __init__(self):
        pass


class CppStatement:
    def __init__(self):
        pass


class CppAssignment(CppStatement):
    def __init__(self, variable: CppVariable, expression: CppExpression):
        self.variable = variable
        self.expression = expression

    def __str__(self):
        return f"{self.variable} = {self.expression};"


class CppBlock:
    def __init__(self, add_curly_brackets=False):
        self.variables = []
        self.return_variables = []
        self.statements = []
        self.add_curly_brackets = add_curly_brackets
        self.types = {}

    def add_variable(self, var: CppVariable):
        self.variables.append(var)
        if var.type_ not in self.types:
            self.types[var.type_] = []
        self.types[var.type_] += [var]

    def add_code(self, code):
        self.statements += [code]

    def __str__(self):
        var_block = (
            (
                "\n".join([f"{var.type_} {var.name};" for var in self.variables]) + "\n"
                if self.variables
                else ""
            )
            if not GROUP_VARIABLES
            else (
                "\n".join(
                    [
                        type_ + " " + ", ".join([str(var) for var in vars_]) + ";\n"
                        for type_, vars_ in self.types.items()
                    ]
                )
                if self.variables
                else ""
            )
        )
        return (
            self.add_curly_brackets * "{\n"
            + var_block
            + "\n".join([str(statement) for statement in self.statements])
            + self.add_curly_brackets * "\n}"
        )


class CppScope:
    def __init__(self, ports, parent_scope=None):
        self.ports = ports
        if parent_scope:
            for port in self.ports:
                port.value = parent_scope.get_port(port.label).value

    def get_port(self, label: str):
        for port in self.ports:
            if port.label == label:
                return port


def cpp_eval(in_port, scope, block, name=None):
    port = Edge.edge_to[in_port.id].from_
    if not port.value:
        if name:
            port.node.to_cpp(scope, block, name)
        else:
            port.node.to_cpp(scope, block)
    in_port.value = port.value
    return in_port.value
