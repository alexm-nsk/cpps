#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""This is the main application that is used from command line as a
stand-alone. Use the parse module in other cases.
"""

import sys
import json
import re
from parser import parse
from os import path
from utils.system import get_piped_input
from parser.parser_state import enable_debug, debug_enabled
from copy import copy

json_re = re.compile("_([a-z])")
re_remove_ = re.compile("_(?=$)")


def json_names(obj):
    """Converts snake_case to camelCase in a dictionary
    and removes '_' at the end"""
    new_object = {}

    def convert(value):
        if isinstance(value, dict):
            return json_names(value)
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    for key, value in obj.items():
        new_key = re.sub(json_re, lambda m: m.group(1).upper(), key)
        new_key = re.sub(re_remove_, "", new_key)
        new_object[new_key] = convert(value)

    return new_object


def main(args):
    """The main function"""
    # check if there is piped-in src_code
    # otherwise load it from specified file
    from signal import signal, SIGPIPE, SIG_DFL
    signal(SIGPIPE, SIG_DFL)

    if "-i" in args:
        file_name_index = args.index("-i") + 1
        if not path.isfile(args[file_name_index]):
            print(f"Error: file {args[1]} not found, or is a directory.")
            return -1

        with open(args[file_name_index], "r", encoding="UTF-8") as src_file:
            src_code = src_file.read()
    else:
        src_code = get_piped_input()

    if "--debug" in args:
        enable_debug()

    parsed_ir = parse.parse(src_code)
    if not parsed_ir["errors"]:
        parsed = copy(parsed_ir)
        parsed["functions"] = [
                function.ir_() for function in parsed["functions"]
            ]
        if "--opt" in args:
            from optimizer.optimize_ir import optimize_ir
            from utils.python_names import python_names
            from ir import module

            module = module.Module()
            module.load_from_json_data(json_names(parsed))
            if "--drawgraph" in args:
                from ir.draw_graph import draw_module
                draw_module(optimize_ir(module))
                return
            parsed = python_names(optimize_ir(module).save_to_json())
        if "--json" in args:
            '''Parse only and try to get an IR as JSON'''
            print(json.dumps(json_names(parsed), indent=1))
        elif "--graphml" in args:
            '''Parse only and try to get an IR as GraphML'''
            import parser.graphml as graphml

            gmlm = graphml.GraphMlModule(parsed_ir)
            print(gmlm)
        elif "--drawgraph" in args:
            from ir.draw_graph import draw_graph
            draw_graph(json_names(parsed))
        else:
            '''Parse and generate a C++ program'''
            import codegen.codegen_state
            codegen.codegen_state.global_no_error = "--noerror" in args
            from code_gen import compile_ir
            module_name = ""  # args[1].split(".")[:-1]
            # convert it to JSON text:
            ir = json.dumps(json_names(parsed), indent=1)
            try:
                cpp_src = compile_ir(ir, module_name)
                # put out a JSON containing the code and errors,
                # or just plain code:
                if "--cppjson" in args:
                    print(json.dumps(
                                 {"errors": [],
                                  "cpp_src": [cpp_src]}
                                ))
                else:
                    print(cpp_src)
            except Exception as e:
                if debug_enabled():
                    raise (e)
                return {"errors": [str(e)], "cpp_src": None}
    else:
        return json.dumps(parsed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
