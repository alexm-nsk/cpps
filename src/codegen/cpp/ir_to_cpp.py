#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""generate cpp"""

from .cpp_codegen import CppModule


def ir_to_cpp(functions: dict):
    print(CppModule(functions))
