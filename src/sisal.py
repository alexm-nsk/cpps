#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""This is the main application that is used from command line as a
stand-alone. Use the parse module in other cases.
"""

import sys
import json
import re
from compiler import parse


def check_piped():
    """Checks if source code is provided via pipe"""
    src_code = ""
    src_code = "".join(sys.stdin)
    return src_code


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
    src_code = ""  # check_piped()
    if src_code == "":
        with open(args[1], "r", encoding="UTF-8") as src_file:
            src_code = src_file.read()
            parsed = parse.parse(src_code)
            if parsed:
                if "--json" in args:
                    parsed["functions"] = [
                            function.ir_()
                            for function in parsed["functions"]
                        ]
                    print(json.dumps(json_names(parsed), indent=1))
                elif "--graphml" in args:
                    parsed["functions"] = [
                            function.ir_()
                            for function in parsed["functions"]
                        ]
                    print(json.dumps(json_names(parsed), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
