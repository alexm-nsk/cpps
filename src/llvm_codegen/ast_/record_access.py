#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator array access
"""

from ..node import Node
from ..llvm.llvm_codegen import llvm_eval
import llvmlite.ir as ll
from ..error import CodeGenError
from ..llvm.llvmlite_helpers import i32zero


class RecordAccess(Node):
    def to_llvm(self, irbuilder: ll.IRBuilder):
        # inputs: array, index

        errored_record = llvm_eval(self.in_ports[0], irbuilder)
        record_error = irbuilder.extract_value(errored_record, 0)
        # prepare error handling
        error_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_err_block"
        )
        no_error_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_correct_exec_block"
        )
        phi_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_phi_block"
        )
        irbuilder.cbranch(record_error, error_block, no_error_block)
        with irbuilder.goto_block(error_block):
            irbuilder.branch(phi_block)
        irbuilder.position_at_start(no_error_block)
        record = irbuilder.extract_value(errored_record, 1)
        indices = record.type.names_to_indices()
        if isinstance(record, ll.PointerType):
            errptr = irbuilder.gep(
                record,
                [i32zero, i32zero],
                source_etype=self.out_ports[0].type.llvm_type(),
            )
            pointer = irbuilder.gep(
                record,
                [i32zero, indices[self.field]],
                source_etype=self.out_ports[0].type.llvm_type(),
            )
            # Cloud Sisal Arrays' indices start from 1 by default
            # hence the {index}-1
            new_var = irbuilder.load(pointer, typ=self.out_ports[0].type.llvm_type())
        else:
            new_var = irbuilder.extract_value(record, indices[self.field])
        o_p = self.out_ports[0]
        no_error_res = o_p.type.pack_val(new_var)
        irbuilder.branch(phi_block)

        with irbuilder.goto_block(error_block):

            error_res = o_p.type.make_error(irbuilder)
            """ 
            res_inner_type = o_p.type.llvm_type()
            error_res = irbuilder.insert_value(
                res_init, res_inner_type(ll.Undefined), 1
            )"""

        irbuilder.position_at_start(phi_block)
        phi = irbuilder.phi(o_p.type.errored_llvm_type())
        phi.add_incoming(error_res, error_block)
        phi.add_incoming(no_error_res, no_error_block)
        o_p.value = phi
