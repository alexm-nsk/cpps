#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""generate cpp"""

from .cpp_codegen import CppModule


def ir_to_cpp(module_name, functions: dict, definitions: dict):
    return CppModule(module_name, functions, definitions)
