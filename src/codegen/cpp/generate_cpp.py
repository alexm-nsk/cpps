#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""generate cpp"""


def generate_cpp(functions: dict):
    for name, function in functions.items():
        print(name, function)
