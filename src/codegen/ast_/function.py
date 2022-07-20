#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""
from ..node import Node, to_cpp_method
from ..cpp.cpp_codegen import (CppBlock,
                               CppVariable,
                               indent_cpp,
                               cpp_eval)


class Function(Node):

    functions = {}
    name = "function"

    copy_parent_input_values = False
    name_child_output_values = True
    result_name = "function_result"

    def num_outputs(self):
        return len(self.out_ports)

    def __init__(self, data):
        super().__init__(data)
        Function.functions[self.function_name] = self

    @property
    def ret_cpp_type(self):
        ret_types = [port.type for port in self.out_ports]
        return ("tuple<" +
                ', '.join([type_.cpp_type for type_ in ret_types]) +
                ">")

    @to_cpp_method
    def to_cpp(self, block=None):
        CppVariable.variable_index = {}
        ret_types = [port.type for port in self.out_ports]

        for port in self.in_ports:
            port.value = CppVariable(port.label, port.type)

        arg_str = ", ".join([port.value.definition_str()
                             for port in self.in_ports])

        function_block = CppBlock()

        for index, o_p in enumerate(self.out_ports):
            cpp_eval(
                o_p,
                function_block,
            )

        cpp_function_name = (
            "sisal_main"
            if self.function_name == "main" else self.function_name
        )

        ret_type_str = (
                        ret_types[0].cpp_type if len(ret_types) == 1
                        else
                        "tuple<" +
                        ', '.join([type_.cpp_type for type_ in ret_types]) +
                        ">"
                        )

        return_value = (
                        f"return {o_p.value};" if len(ret_types) == 1
                        else
                        "return {" +
                        ", ".join([str(o_p.value) for o_p in self.out_ports]) +
                        "};"
                        )

        function_string = (
            f"{ret_type_str} {cpp_function_name}({arg_str})\n"
            "{\n"
            + indent_cpp(str(function_block))
            + "\n"
            + indent_cpp(return_value)
            + "\n}"
        )

        return function_string


def create_main():
    """ creates a C++ main(...) that loads JSON input data from a stdin
        and outputs data as JSON to stdout
    """
    main = Function.functions["main"]

    body = (
        "Json::Value root;\n"
        "std::cin >> root;\n"
        "Json::Value json_result;\n"
    )

    body += "\n".join([port.value.get_load_from_json_code(
                                f'root["{port.value.name}"]'
                            ) + ""
                       for port in main.in_ports]) + "\n"

    if main.num_outputs() == 1:
        sisal_main_result = ("sisal_main(" +
                             ', '.join([str(port.value)
                                        for port in main.in_ports]) +
                             ");")

        body += main.out_ports[0].type.save_to_json_code("json_result",
                                                         sisal_main_result)
    else:
        body += f"{main.ret_cpp_type} main_result = " +\
                ("sisal_main(" +
                 ', '.join([str(port.value) for port in main.in_ports]) +
                 ");") + ";\n"

        for index, o_p in enumerate(main.out_ports):
            body += (o_p.type.save_to_json_code(
                        f"json_result[{index}]",
                        f"get<{o_p.type.cpp_type}>(main_result{[index]})") +
                     "\n")

    result_output_code = ('std::cout << json_result << "\\n";\n'
                          'std::cout << std::endl;')

    return (
            "int main(int argc, char **argv)\n"
            "{\n"
            f"{indent_cpp(body)}\n"
            f"{indent_cpp(result_output_code)}\n"
            f"{indent_cpp('return 0;')}"
            "\n}"
            )
