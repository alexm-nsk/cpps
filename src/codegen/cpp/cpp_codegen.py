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
    indent = indent_level * CPP_INDENT
    return indent + src_code.replace("\n", "\n" + indent)


class CppVariable:

    variable_index = {}

    def __init__(self, name, type_, value=None):
        self.type_ = type_
        self.name = name
        self.value = value

    def __repr__(self):
        return f"CppVariable<{self.name}, {self.type_}, {self.value}>"

    def __str__(self):
        return self.name

    def definition_str(self):
        return f"{self.type_.cpp_type} {self.name}"


class CppModule:
    def __init__(self, name: str, functions: dict, definitions: list = []):
        self.modules = []
        for name, f in functions.items():
            self.modules += [f.to_cpp()]

    def __str__(self):
        return CPP_MODULE_HEADER + "\n\n".join(self.modules)


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

    def add_variable(self, var: CppVariable):
        self.variables.append(var)

    def add_code(self, code):
        self.statements += [code]

    def __str__(self):

        return (
            self.add_curly_brackets * "{\n"
            + "\n".join(self.statements)
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
