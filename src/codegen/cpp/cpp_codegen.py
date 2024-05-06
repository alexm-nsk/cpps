#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""C++ code generation"""
from ..edge import Edge
from ..type import AnyType, ArrayType, RecordType
from string import Template
from ..codegen_state import global_no_error
import os

GROUP_VARIABLES = True

CPP_INDENT = "  "
CPP_MODULE_HEADER = (
    """\
#include <stdio.h>
#include <omp.h>
#include <vector>
#include <iostream>
#include <fstream>
#include <string>
#include <json/json.h> // uses jsoncpp library
$sisal_types_h
$extra_headers"""
    + """
#define integer int
#define real float
#define boolean bool
#define Array std::vector

"""
    * global_no_error
    + """#define CHECK_INPUT_ARGUMENT(arg) if(root[arg].isNull())\\
  {\\
    Json::Value error;\\
    std::string message = arg;\\
    message.append(" not found in input data.");\\
    error["errors"].append(message);\\
    error["code"].append("null");\\
    std::cout << error << "\\n";\\
    std::cout << std::endl;\\
    return 1;\\
  }\\

template <typename I>
inline Array<I> addh (const Array<I> A, auto item)
{
  Array<I> result = A;
  result.push_back(item);
  return result;
}

template <typename I>
inline Array<I> remh (const Array<I> A)
{
  Array<I> result = A;
  result.pop_back();
  return result;
}

template <typename I>
inline Array<I> reml (const Array<I> A)
{
  Array<I> result = A;
  result.pop_front();
  return result;
}

template <typename I>
inline Array<I> addl (const Array<I> A, auto item)
{
  Array<I> result = A;
  result.push_front(item);
  return result;
}

inline unsigned int size (Array<auto> A)
{
  return A.size();
}

//------------------------------------------------------------
"""
)


def indent_cpp(src_code, indent_level=1, indent_first=True):
    """indents src_code
    indent_level - how many CPP_INDENTs will be added,
    indent_first - should the first line be indented
    """
    indent = indent_level * CPP_INDENT
    return indent * indent_first + src_code.replace("\n", "\n" + indent)


class CppVariable:
    """Holds C++ variables"""

    variable_index = {}

    def init_code(self):
        # it has to be "!= None" (not "if self.value:"),
        # otherwise 0 would trigger it too
        if self.value != None:
            return self.name + " = " + str(self.value)
        else:
            return self.name

    @staticmethod
    def get_name(name):
        if not name:
            name = "var"

        if name not in CppVariable.variable_index:
            CppVariable.variable_index[name] = 0

        CppVariable.variable_index[name] += 1

        if CppVariable.variable_index[name] > 1:
            name = name + str(CppVariable.variable_index[name])

        return name

    def __init__(self, name, type_, value=None):
        self.type_ = type_
        self.name = CppVariable.get_name(name)

        self.value = value

    def __repr__(self):
        return f"CppVariable<{self.name}, {self.type_}, {self.value}>"

    def __str__(self):
        return self.name

    def definition_str(self):
        return f"{self.type_.cpp_type} {self.name}"

    def get_load_from_json_code(self, json_object=None):
        return self.type_.load_from_json_code(self.name, json_object)


class CppModule:
    def __init__(self, name: str, functions: dict, definitions: dict = {}):
        self.functions = []
        self.extra_headers = []
        self.prototypes = []
        self.service_classes = []
        for name, f in functions.items():
            f.module = self
            self.functions += [f.to_cpp(None)]
            self.add_prototype(f)

        from ..ast_.function import create_main

        self.functions += [create_main()]

        self.definitions = [
            f"typedef {type_.internal_type} {def_};\n"
            for def_, type_ in definitions.items()
        ]

    def add_header(self, name: str):
        if name not in self.extra_headers:
            self.extra_headers.append(name)

    def add_service_class(self, service_class):
        self.service_classes.append(service_class)

    def add_prototype(self, function):
        self.prototypes.append(function.get_cpp_prototype())

    def __str__(self):
        m_h_template = Template(CPP_MODULE_HEADER)
        extra_headers_str = "\n".join([f"#include <{h}>" for h in self.extra_headers])
        path = os.path.dirname(os.path.abspath(__file__))
        if global_no_error:
            sisal_types_h_str = ""
        else:
            sisal_types_h_str = "\n" + open(path + "/sisal_types.h", "r").read()

        module_header = m_h_template.substitute(
            extra_headers=extra_headers_str, sisal_types_h=sisal_types_h_str
        )

        return (
            module_header
            + "\n\n".join(
                [struct["string"] for _, struct in RecordType.cpp_structs.items()]
            )
            + "\n\n"
            + "\n\n".join(self.definitions)
            + "\n".join(self.prototypes)
            # + "\n\n"
            + "\n".join(self.service_classes)
            + "\n\n"
            + "\n\n".join(self.functions)
        )


class CppExpression:
    def __init__(self):
        pass


class CppStatement:
    def __init__(self):
        pass


class CppAssignment(CppStatement):
    """Creates a statement like var = value;"""

    def __init__(self, variable: CppVariable, expression: CppExpression):
        self.variable = variable
        self.expression = expression

    def __str__(self):
        return f"{self.variable} = {self.expression};"


class CppBlock:
    """Holds a block of C++ code. Includes variable declarations
    and 3 lists of statements: head(always before others),
    regular and tail (always at the end)
    str method assembles a string containing C++ code for the entire block"""

    def __init__(self, add_curly_brackets=False, indent_contents=False):
        self.variables = []
        # self.return_variables = []
        self.statements = []
        self.add_curly_brackets = add_curly_brackets
        self.types = {}
        self.indent_contents = indent_contents
        self.head_statements = []
        self.tail_statements = []

    def add_variable(self, var: CppVariable):
        self.variables.append(var)
        if var.type_ not in self.types:
            self.types[var.type_] = []
        self.types[var.type_] += [var]

    # add arbitrary code to this block:
    def add_code(self, code):
        self.statements += [code]

    def add_head_code(self, code):
        self.head_statements += [code]

    def add_tail_code(self, code):
        self.tail_statements += [code]

    @property
    def all_statements(self):
        return self.head_statements + self.statements + self.tail_statements

    def __str__(self):
        """Turn this block into a string"""
        var_block = (
            (
                "\n".join([f"{var.type_} {var.init_code()};" for var in self.variables])
                if self.variables
                else ""
            )
            if not GROUP_VARIABLES
            else (
                "\n".join(
                    [
                        type_
                        + " "
                        + ", ".join([str(var.init_code()) for var in vars_])
                        + ";"
                        for type_, vars_ in self.types.items()
                    ]
                )
                if self.variables
                else ""
            )
        )
        ret_val = (
            self.add_curly_brackets * "{\n"
            + (
                (indent_cpp(var_block) if self.indent_contents else var_block)
                if var_block
                else ""
            )
            + ("\n" if self.variables and self.statements else "")
            + "\n".join(
                [
                    indent_cpp(str(statement))
                    if self.indent_contents
                    else str(statement)
                    for statement in self.all_statements
                ]
            )
            + self.add_curly_brackets * "\n}"
        )

        return ret_val


def cpp_eval(in_port, block):
    """Calculates the value for specified port (in_port),
    if value isnt present in the specified port, and assigns that value to
    the port.
    Returns the calculated value.
    """
    port = Edge.edge_to[in_port.id].from_

    if not port.value:
        port.node.to_cpp(block)
    in_port.value = port.value
    return in_port.value
