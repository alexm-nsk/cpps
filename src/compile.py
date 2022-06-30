#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""Deserializes json IRs"""

import sys


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
            if file_name.lower().endswith(".gml"):
                pass
            elif file_name.lower().endswith(".json"):
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
