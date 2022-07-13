#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""
from ..node import Node
from ..cpp.cpp_codegen import (CppScope,
                               CppBlock,
                               CppVariable,
                               indent_cpp,
                               cpp_eval)


class Function(Node):

    functions = {}

    def __init__(self, data):
        super().__init__(data)
        Function.functions[self.function_name] = self

    def to_cpp(self):
        CppVariable.variable_index = {}
        ret_type = self.out_ports[0].type

        for port in self.in_ports:
            port.value = CppVariable(port.label, port.type)

        this_function_scope = CppScope(self.in_ports)

        arg_str = ", ".join([port.value.definition_str()
                             for port in self.in_ports])

        function_block = CppBlock()

        for index, o_p in enumerate(self.out_ports):
            cpp_eval(
                o_p,
                this_function_scope,
                function_block,
                self.function_name + "_result_" + str(index + 1),
            )

        cpp_function_name = (
            "sisal_main"
            if self.function_name == "main" else self.function_name
        )

        function_string = (
            f"{ret_type.cpp_type} {cpp_function_name}({arg_str})\n"
            "{\n"
            + indent_cpp(str(function_block))
            + "\n"
            + indent_cpp(f"return {o_p.value};")
            + "\n}"
        )

        return function_string


def create_main():
    main = Function.functions["main"]

    body = (
        "Json::Value root;\n"
        "std::cin >> root;\n"
    )

    body += "\n".join([port.value.get_load_from_json_code(
                                f'root["{port.value.name}"]'
                            ) + ";"
                       for port in main.in_ports]) + "\n"

    from ..type import get_type

    type_object = get_type({
                                "location": "1:42-1:58",
                                "element": {
                                    "location": "1:51-1:58",
                                    "element": {
                                        "location": "1:51-1:58",
                                        "name": "integer"
                                    },
                                    "multi_type": "array"
                                },
                                "multi_type": "array"
                            })

    print(type_object.load_from_json_code("A", "root[\"A\"]"))

    body += ("result = "
             "sisal_main(" +
             ', '.join([str(port.value) for port in main.in_ports]) +
             ");")

    init_result = "Json::Value result;"

    result_output_code = ('std::cout << result << "\\n";\n'
                          'std::cout << std::endl;')

    return (
            "int main(int argc, char **argv)\n"
            "{\n"
            f"{indent_cpp(init_result)}\n"
            f"{indent_cpp(body)}\n"
            f"{indent_cpp(result_output_code)}\n"
            f"{indent_cpp('return 0;')}"
            "\n}"
            )
