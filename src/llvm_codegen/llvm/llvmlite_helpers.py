import llvmlite.ir as ll

i1 = ll.IntType(1)
i32 = ll.IntType(32)
i64 = ll.IntType(64)

i32zero = i32(0)
i32one = i32(1)

<<<<<<< HEAD
=======
copy_array_to_new_addr_loops = {}


def copy_array_to_new_addr_loop(elemtype, irbuilder: ll.IRBuilder):
    try:
        return copy_array_to_new_addr_loops[elemtype]
    except:
        loop_func_type = ll.FunctionType(
            ll.VoidType(),
            [ll.PointerType(), ll.PointerType(), ll.IntType(32)],  # oldptr,newptr,len
        )
        loop_func = ll.Function(
            irbuilder.module, loop_func_type, name="copy_array_to_new_addr"
        )
        entry = loop_func.append_basic_block("entry")
        header = loop_func.append_basic_block("loop_header")
        body = loop_func.append_basic_block("loop_body")
        exit = loop_func.append_basic_block("loop_exit")
        with irbuilder.goto_block(entry):
            zero_cond = irbuilder.icmp_signed(
                "==", ll.Constant(ll.IntType(32), 0), loop_func.args[2]
            )
            irbuilder.cbranch(zero_cond, exit, header)
        with irbuilder.goto_block(header):
            count = irbuilder.phi(ll.IntType(32))
            cond = irbuilder.icmp_signed("<", count, loop_func.args[2])
            count.add_incoming(ll.Constant(ll.IntType(32), 0), entry)
            irbuilder.cbranch(cond, body, exit)
        with irbuilder.goto_block(body):
            elemptr = irbuilder.gep(
                loop_func.args[0],
                [ll.Constant(ll.IntType(32), 0), count],
                source_etype=elemtype,
            )
            elem = irbuilder.load(elemptr, typ=elemtype)
            newelemptr = irbuilder.gep(
                loop_func.args[1],
                [ll.Constant(ll.IntType(32), 0), count],
                source_etype=elemtype,
            )
            irbuilder.store(elem, newelemptr)
            new_count = irbuilder.add(count, ll.Constant(ll.IntType(32), 1))
            count.add_incoming(new_count, body)
            irbuilder.branch(header)
        with irbuilder.goto_block(exit):
            irbuilder.ret_void()
        copy_array_to_new_addr_loops[elemtype] = loop_func
        return loop_func

>>>>>>> 2f1e8e2 (i merely renamed codegen folder....)

def printf_str(irbuilder, printf, str_val):
    c_str_val = ll.Constant(
        ll.ArrayType(ll.IntType(8), len(str_val)), bytearray(str_val.encode("utf-8"))
    )
    c_str = irbuilder.alloca(c_str_val.type)
    irbuilder.store(c_str_val, c_str)
    irbuilder.call(printf, [c_str])


memsizes = {}


def calc_memsize_at_runtime(irbuilder: ll.IRBuilder, element_type, count):
    try:
        return memsizes[irbuilder.function][element_type][count]
    except:
        """
        Generate IR that computes the size at runtime using GEP arithmetic.
        This avoids needing the size at IR generation time.
        """
        # Create a dummy allocation of 1 element
        dummy = irbuilder.alloca(element_type)
        if type(count) == int:
            new_count = i32(count)
        else:
            new_count = count
        # Create a GEP at index 'count' and get the byte difference
        # This works because LLVM's GEP uses type sizes internally
        ptr_start = irbuilder.ptrtoint(dummy, i64)
        ptr_end = irbuilder.gep(dummy, [new_count])
        ptr_end_casted = irbuilder.ptrtoint(ptr_end, i64)

        size = irbuilder.sub(ptr_end_casted, ptr_start)
        if not irbuilder.function in memsizes:
            memsizes[irbuilder.function] = {}
        if not element_type in memsizes[irbuilder.function]:
            memsizes[irbuilder.function][element_type] = {}
        memsizes[irbuilder.function][element_type][count] = size
        return size


def create_error_handling_blocks(node, irbuilder: ll.IRBuilder):
    # prepare error handling
    error_block = irbuilder.append_basic_block(
        f"{node.name if hasattr(node,'name') else node.__class__.__name__ }_err_block"
    )
    no_error_block = irbuilder.append_basic_block(
        f"{node.name if hasattr(node,'name') else node.__class__.__name__ }_correct_exec_block"
    )
    phi_block = irbuilder.append_basic_block(
        f"{node.name if hasattr(node,'name') else node.__class__.__name__ }_phi_block"
    )
    with irbuilder.goto_block(error_block):
        irbuilder.branch(phi_block)
    return error_block, no_error_block, phi_block
