#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
from codegen.load_json import load_json
from codegen.load_graphml import load_graphml
from codegen.parse_ir import parse_ir


def check_piped():
    """Checks if source code is provided via pipe"""
    input_text = ""
    input_text = "".join(sys.stdin)
    return input_text


def main(args):
    """The main function"""
    # check if there is piped-in input_text
    # otherwise load it from specified file
    file_name = args[1]
    input_text = ""  # check_piped()
    if input_text == "":
        with open(file_name, "r", encoding="UTF-8") as src_file:
            input_text = src_file.read()
            if file_name.lower().endswith(".json"):
                ir_ = load_json(input_text)
            elif file_name.lower().endswith(".gml"):
                ir_ = load_graphml(input_text)
            functions = parse_ir(ir_)
            from codegen.cpp.ir_to_cpp import ir_to_cpp
            ir_to_cpp(functions)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
