#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""Deserializes json IRs"""

import sys

def main(args):
    """The main function"""
    # check if there is piped-in src_code
    # otherwise load it from specified file
    src_code = ""  # check_piped()
    if src_code == "":
        with open(args[1], "r", encoding="UTF-8") as src_file:
            src_code = src_file.read()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
