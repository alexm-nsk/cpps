#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""generate llvm"""

from .llvm_codegen import LlModule


def ir_to_llvm(module_name, functions: dict, definitions: dict):
    return LlModule(module_name, functions, definitions)


def ir_to_bitcode(ir: LlModule, target_triple):
    return ir.bitcode_gen(target_triple)


def run_through_llvmlite(ir: LlModule, args: dict):
    argvals = []
    vars = ir.get_input_names()  # methods for reading input lists?
    for var in vars:
        try:
            argvals.append(args[var])
        except Exception as e:
            print(e + f"\nVariable {var} not provided")
    return ir.run_on_jit(argvals)
