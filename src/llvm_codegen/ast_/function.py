#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator function
"""

from ..node import Node, to_llvm_method
from ..llvm.llvm_codegen import llvm_eval, LlModule, heap_allocation_helper
from ..error import CodeGenError
from ..type import ArrayType, printf_str, get_array_descriptor
import llvmlite.ir as ll


class Function(Node):

    functions = {}
    name = "function"
    service_function_counter = 0
    copy_parent_input_values = False
    name_child_output_values = True
    result_name = "function_result"

    @staticmethod
    def get_service_name(name):
        Function.service_function_counter += 1
        new_name = f"service_function{Function.service_function_counter}_for_" + name
        while new_name in Function.functions:
            Function.service_function_counter += 1
            new_name = (
                f"service_function{Function.service_function_counter}_for_" + name
            )
        return new_name

    @property
    def num_outputs(self):
        return len(self.out_ports)

    def __init__(self, data):
        super().__init__(data)
        if "dont_register" not in data or not data["dont_register"]:
            Function.functions[self.function_name] = self
        self.mallocs = set()
        self.preserved_mallocs = set()

    @to_llvm_method
    def to_llvm(self, irbuilder: ll.IRBuilder):
        # mark nodes that contribute to (currently) creating output arrays, so those are preserved during memory freeing
        self.mark_heap_allocation()

        # collect ir types corresponding to arg types in a list:
        # args = [port.type.llvm_type() for port in self.in_ports]
        args = [port.type.errored_llvm_type() for port in self.in_ports]
        # collect ir types corresponding to return types in a list:
        # ret_types = [port.type.llvm_type() for port in self.out_ports]
        ret_types = [port.type.errored_llvm_type() for port in self.out_ports]
        # format types for llvmlite
        if len(ret_types) == 0:
            ret_type = ll.VoidType()
        else:
            if len(ret_types) == 1:
                ret_type = ret_types[0]
            else:
                ret_type = ll.LiteralStructType(ret_types)
        # make a corresponding function type
        func_type = ll.FunctionType(ret_type, args)

        # choose an appropriate name for the function (renaming main might be needed if end up adding default input-output function):
        self.ir_function_name = (
            "sisal_main" if self.function_name == "main" else self.function_name
        )
        # make a function object
        func = ll.Function(
            module=self.module, ftype=func_type, name=self.ir_function_name
        )
        entry_block = func.append_basic_block(name="entry")
        irbuilder.position_at_start(entry_block)
        # save datatypes for later use in jit call (to do move to sep method with other main-exclusive processing)
        if self.function_name == "main":
            irbuilder.module.set_inputs(
                {port.label: port.type for port in self.in_ports}
            )
        # assign arguments to temp vars:
        for port, arg in zip(self.in_ports, func.args):
            port.value = arg
        # evaluate function output values (results):
        ret_vals = []
        for index, o_p in enumerate(self.out_ports):
            llvm_eval(o_p, irbuilder)
            ret_vals.append(o_p.value)

        # free heap-allocated memory:
        mallocs_to_rem = self.mallocs - self.preserved_mallocs
        for ptr in mallocs_to_rem:
            irbuilder.call(irbuilder.module.free, [ptr])
        # form ret value:
        if len(ret_vals) == 1:
            ret_val = ret_vals[0]
        elif isinstance(ret_type, ll.VoidType):
            irbuilder.ret_void()
        else:
            ret_val = ll.Constant(ret_type, None)
            for index, val in enumerate(ret_vals):
                ret_val = irbuilder.insert_value(ret_val, val, index)

        irbuilder.ret(ret_val)

        # check if we requested time_out (time limiting) and process that:
        # self.process_timeout()

        return func

    def mark_heap_allocation(self):
        for o_p in self.out_ports:
            if isinstance(o_p.type, ArrayType):
                o_p.type.is_output_array = True
                heap_allocation_helper(o_p)


# TODO and i do need to make vals packing in main, ofc
# or perhaps even in ctypes
def create_main(irbuilder: ll.IRBuilder):
    # passes down args and provides console output
    if "main" not in Function.functions:
        raise CodeGenError("Module must contain main-function.")
    main_ir = Function.functions["main"]
    main_ib = irbuilder.module.get_global("sisal_main")
    args = [i_p.type.llvm_type() for i_p in main_ir.in_ports]
    main_type = ll.FunctionType(ll.IntType(32), args)
    main = ll.Function(irbuilder.module, main_type, "main")
    block = main.append_basic_block()
    irbuilder.position_at_start(block)

    """input_str_type = lambda len: ll.ArrayType(ll.IntType(8), len)
    scanf_types = {
        "int_input": ll.GlobalVariable(irbuilder.module, input_str_type(3)),
        "lint_input": ll.GlobalVariable(irbuilder.module, input_str_type(4)),
        "llint_input": ll.GlobalVariable(irbuilder.module, input_str_type(5)),
        "float_input": ll.GlobalVariable(irbuilder.module, input_str_type(3)),
        "char_input": ll.GlobalVariable(irbuilder.module, input_str_type(3)),
        "str_input": ll.GlobalVariable(irbuilder.module, input_str_type(3)),
    }
    scanf_types["int_input"].initializer = ll.Constant(input_str_type(3), "%d\00")
    scanf_types["lint_input"].initializer = ll.Constant(input_str_type(4), "%ld\00")
    scanf_types["llint_input"].initializer = ll.Constant(input_str_type(5), "%lld\00")
    scanf_types["float_input"].initializer = ll.Constant(input_str_type(3), "%f\00")
    scanf_types["char_input"].initializer = ll.Constant(input_str_type(3), "%c\00")
    scanf_types["str_input"].initializer = ll.Constant(input_str_type(3), "%s\00")
    scanf_inputs = {
        "int_input": ll.GlobalVariable(irbuilder.module, ll.IntType(64)),
        "float_input": ll.GlobalVariable(irbuilder.module, ll.DoubleType),
    }
    argvals = []
    for arg in args:
        typ = type(arg)
        typname = ""
        if isinstance(typ, ll.IntType):
            typname = "int_input"
        else:
            if isinstance(typ, ll.DoubleType):
                typname = "float_input"
        if not irbuilder.module.get_global(typname):
            irbuilder.module.add_global(scanf_types[typname])
            scanf_type = ll.FunctionType(
                ll.IntType(32), [ll.PointerType()], var_arg=True
            )
            scanf = ll.Function(module=irbuilder.module, ftype=scanf_type, name="scanf")
            irbuilder.call(scanf, [scanf_types[typname], scanf_inputs[typname]])
            argval = irbuilder.load(scanf_inputs[typname])
            argvals.append(argval)
        # установить тип инта по умолчанию и делать trunc/extend инпута
        res = irbuilder.call(main_ib, argvals)
        """
    # перенести типы для принта/скана в местный тип
    # и билдить вот это параллельно с sisal_main
    # тем более что у нас есть main_ir
    irbuilder.module.set_output({})
    printf = irbuilder.module.printf
    errored_args = [
        (i_p.type.pack_input(arg, irbuilder))
        for i_p, arg in zip(main_ir.in_ports, main.args)
    ]
    res = irbuilder.call(main_ib, errored_args)
    str_val = "{\n\00"
    printf_str(irbuilder, printf, str_val)
    if len(main_ir.out_ports) > 1:

        for i, o_p in enumerate(main_ir.out_ports):
            val = irbuilder.extract_value(
                res,
                i,
            )
            if i > 0:
                str_val = ",\n\00"
                printf_str(irbuilder, printf, str_val)
            o_p.type.add_printf(irbuilder, printf, val, f"port{i}")

    else:
        main_ir.out_ports[0].type.add_printf(
            irbuilder, printf, res, main_ir.out_ports[0].label
        )
    str_val = "\n}\00"
    printf_str(irbuilder, printf, str_val)

    irbuilder.ret(ll.Constant(ll.IntType(32), 0))
