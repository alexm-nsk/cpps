#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""
from ..node import Node, to_cpp_method
from ..cpp.cpp_codegen import (CppBlock,
                               CppVariable,
                               CppAssignment,
                               indent_cpp,
                               cpp_eval)
from ..error import CodeGenError
from ..cpp import template
from ..codegen_state import global_no_error


def gen_time_limit_template(function):

    class_template = template.load_template("time_out_class.cpp")

    '''generate return values assignments:'''
    block = CppBlock()

    arg_vars = ["f->" + i_p.label for i_p in function.in_ports]
    args = ", ".join(arg_vars)

    block.add_code(CppAssignment("f->retval",
                                 f"{function.cpp_function_name}({args})"))

    write_retvals = indent_cpp(str(block), 2, indent_first=False)

    # generate arguments declaration
    args = "\n".join([str(i_p.type.cpp_type) + " " + i_p.label + ";"
                      for i_p in function.in_ports])

    # generate retvals declaration
    declare_retvals = function.ret_type_str + " " + "retval" + ";"

    # generate code that will copy the args:
    copy_args = "\n".join([f"this->{i_p.label}" + " = " + i_p.label + ";"
                           for i_p in function.in_ports])

    # generate args as parameters:
    call_args = ", ".join([str(i_p.type.cpp_type) + " " + i_p.label
                           for i_p in function.in_ports])

    set_error_value = "retval.set_error();" if not global_no_error else ""

    inserts = dict(write_retvals=write_retvals,
                   args=args,
                   declare_retvals=declare_retvals,
                   copy_args=copy_args,
                   call_args=call_args,
                   set_error_value=set_error_value,
                   class_name=function.cpp_function_name.title() +
                   "ExecutionManager")

    class_str = class_template.substitute(inserts)
    return class_str


def time_limited_execution_cpp(function, args: str):
    block = CppBlock()
    if hasattr(function, "cpp_function_name"):
        code = function.cpp_function_name.title() + "ExecutionManager"
    else:
        code = function.function_name.title() + "ExecutionManager"
    #TODO add error handling here (pragma not there etc.)
    pragma_timeout = function.get_pragma("max_time")
    time = pragma_timeout["args"][0]
    class_object_name = CppVariable.get_name("exec_man")
    code += f" {class_object_name}({args}, {time});"
    block.add_code(code)
    return str(class_object_name), str(block)


class Function(Node):

    functions = {}
    name = "function"
    service_function_counter = 0
    copy_parent_input_values = False
    name_child_output_values = True
    result_name = "function_result"

    @staticmethod
    def get_service_name(name):
        Function.service_function_counter += 1
        new_name = f"service_function{Function.service_function_counter}_for_" + name
        while new_name in Function.functions:
            Function.service_function_counter += 1
            new_name = f"service_function{Function.service_function_counter}_for_" + name
        return new_name

    @property
    def num_outputs(self):
        return len(self.out_ports)

    def __init__(self, data):
        super().__init__(data)
        if "dont_register" not in data or not data["dont_register"]:
            Function.functions[self.function_name] = self

    @property
    def ret_cpp_type(self):
        if self.num_outputs > 1:
            ret_types = [port.type for port in self.out_ports]
            return "tuple<" + ", ".join([type_.cpp_type
                                         for type_ in ret_types]) + ">"
        else:
            return self.out_ports[0].type.cpp_type

    def get_cpp_prototype(self):
        ret_types = [port.type for port in self.out_ports]
        ret_type_str = (
            ret_types[0].cpp_type
            if len(ret_types) == 1
            else "tuple<" + ", ".join([type_.cpp_type
                                       for type_ in ret_types]) + ">"
        )
        cpp_function_name = (
            "sisal_main" if self.function_name == "main"
            else self.function_name
        )
        arg_str = ", ".join([port.value.definition_str()
                             for port in self.in_ports])

        return f"{ret_type_str} {cpp_function_name}({arg_str});"

    def process_timeout(self):
        if hasattr(self, "pragmas"):
            time_out = next((p for p in self.pragmas if p["name"] == "max_time")
                         , None)
            if time_out:
                self.module.add_header("pthread.h")
                inserts = gen_time_limit_template(self)
                self.module.add_service_class(inserts)

    @to_cpp_method
    def to_cpp(self, block=None):
        # reset variable index:
        CppVariable.variable_index = {}

        # collect return types in a list:
        ret_types = [port.type for port in self.out_ports]

        # assign arguments to C++ vars:
        for port in self.in_ports:
            port.value = CppVariable(port.label, port.type)

        arg_str = ", ".join([port.value.definition_str()
                             for port in self.in_ports])

        # initialize a block of C++ code for function body:
        function_block = CppBlock()

        # evaluate function output values (results):
        for index, o_p in enumerate(self.out_ports):
            cpp_eval(
                o_p,
                function_block,
            )

        # select appropriate name for the C++ function
        # (rename it if it is main):
        self.cpp_function_name = (
            "sisal_main" if self.function_name == "main"
            else self.function_name
        )

        # generate C++ return types:
        self.ret_type_str = (
            ret_types[0].cpp_type
            if len(ret_types) == 1
            else "tuple<" + ", ".join([type_.cpp_type
                                       for type_ in ret_types]) + ">"
        )

        # generate results return code
        return_value = (
            f"return {o_p.value};"
            if len(ret_types) == 1
            else "return {"
            + ", ".join([str(o_p.value) for o_p in self.out_ports])
            + "};"
        )

        # convert the block to string:
        str_function_block = str(function_block)

        # check if we requested time_out (time limiting) and process that:
        self.process_timeout()

        # assemble the final string:
        function_string = (
            f"{self.ret_type_str} {self.cpp_function_name}({arg_str})\n"
            "{\n"
            + (indent_cpp(str_function_block) + "\n"
               if str_function_block else "")
            + indent_cpp(return_value)
            + "\n}"
        )

        return function_string


def create_main():
    """Creates a C++ main(...) that loads JSON input data from stdin
    and outputs data as JSON to stdout.
    """
    if "main" not in Function.functions:
        raise CodeGenError("Module must contain main-function.")
    main = Function.functions["main"]

    body = ("Json::Value root;\n"
            "std::cin >> root;\n"
            "Json::Value json_result;\n")

    # check if needed values are passed to the program:

    for port in main.in_ports:
        body += f"CHECK_INPUT_ARGUMENT(\"{port.value.name}\");\n"

    # add code that loads values from input JSON

    body += (
        "\n".join(
            [
                port.value.get_load_from_json_code(
                    f'root["{port.value.name}"]') +
                ""
                for port in main.in_ports
            ]
        )
        + "\n"
    )

    args = ", ".join([str(port.value)
                      for port in main.in_ports])

    time_out = main.get_pragma("max_time")
    if time_out:
        class_object_name, added_code = time_limited_execution_cpp(main, args)
        body += added_code + "\n"
        sisal_main_call = class_object_name + ".retval"
    else:
        sisal_main_call = (
            "sisal_main(" + args + ")"
        )

    #  sisal_main_result = main.

    if main.num_outputs == 1:
        body += f"{main.ret_cpp_type} main_result = " + sisal_main_call + ";\n"
        body += main.out_ports[0].type.save_to_json_code(
            'json_result["port0"]', "main_result"
        )
    else:

        body += f"{main.ret_cpp_type} main_result = " + sisal_main_call + ";\n"
        for index, o_p in enumerate(main.out_ports):
            body += (
                o_p.type.save_to_json_code(
                    f'json_result["port{index}"]', f"get<{index}>(main_result)"
                )
                + "\n"
            )

    result_output_code = (
        'std::cout << json_result << "\\n";\n' "std::cout << std::endl;"
    )

    return (
        "int main(int argc, char **argv)\n"
        "{\n"
        f"{indent_cpp(body)}\n"
        f"{indent_cpp(result_output_code)}\n"
        f"{indent_cpp('return 0;')}"
        "\n}"
    )
