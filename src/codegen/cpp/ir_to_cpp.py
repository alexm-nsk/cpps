#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""generate cpp"""

from .cpp_codegen import *


def ir_to_cpp(functions: dict):
    for name, function in functions.items():
        print(name, function)
