#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""C++ code generation"""
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
    indent = indent_level*CPP_INDENT
    return indent + src_code.replace("\n", "\n" + indent)


class Variable:

    def __init__(self, name, type_, value = None):
        self.type_ = type_
        self.name = name
        self.value = value

    def __repr__(self):
        return f"CppVariable<{self.name}, {self.type_}, {self.value}>"

    def definition_str(self):
        return f"{self.type_.cpp_type} {self.name}"


class CppModule:

    def __init__(self, name: str, functions: dict, definitions: list = []):
        self.modules = []
        for name, f in functions.items():
            self.modules += [f.to_cpp()]

    def __str__(self):
        return CPP_MODULE_HEADER + "\n\n".join(self.modules)


class CppBlock:

    def __init__(self):
        self.variables = []
        self.variable_index = {}

    def add_variable(self, var: Variable):
        self.variables.append(var)
        self.variable_index[var.name] = var


class CppScope:

    def __init__(self, ports, parent_scope = None):
        self.ports = ports
        if parent_scope:
            for port in self.ports:
                port.value = parent_scope.get_port(port.label).value

    def get_port(self, label: str):
        for port in self.ports:
            if port.label == label:
                return port
