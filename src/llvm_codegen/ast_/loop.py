from ..node import Node, to_llvm_method
from ..llvm.llvm_codegen import llvm_eval, heap_allocation_helper
from ..error import CodeGenError
from ..edge import Edge, get_src_node
from ..port import copy_port_values, copy_port_labels
from ..type import ArrayType, get_array_descriptor
from ..llvm.llvmlite_helpers import (
    i32,
    i32zero,
    i32one,
    i64,
    calc_memsize_at_runtime,
    i1,
)

# from ..cpp import template
# from ..codegen_state import global_no_error
import llvmlite.ir as ll

array_descriptor_type = get_array_descriptor()


class LoopExpression(Node):

    count = 0

    copy_parent_input_values = True

    def __init__(self, data):
        super().__init__(data)
        self.reduction_values = []
        self.reduction_operators = []
        self.private_vars = []
        self.ranged = False
        self.left_boundary = None
        self.right_boundary = None
        for node_name in ["init", "body", "condition", "range_gen", "returns"]:
            if node_name not in self.__dict__:
                # for easy checks:
                self.__dict__[node_name] = None
            else:
                # copy LoopObject reference to all it's subnodes:
                self.__dict__[node_name].loop_object = self
                for node in self.__dict__[node_name].nodes:
                    node.loop_object = self

    def mark_heap_allocation(self):
        for o_p, r_o_p in zip(self.out_ports, self.returns.out_ports):
            if (
                hasattr(o_p.type, "is_output_array")
                and o_p.type.is_output_array == True
            ):
                if hasattr(r_o_p.type, "is_output_array"):
                    r_o_p.type.is_output_array = True
                    heap_allocation_helper(r_o_p)
                else:
                    raise CodeGenError("Type mismatch in loop")
        for r_i_p in self.returns.in_ports:
            if hasattr(r_i_p.type, "is_output_array") and r_i_p.type.is_output_array:
                b_o_p = next(
                    port
                    for port in self.loop_object.body.out_ports
                    if port.label == r_i_p.label
                )
                if (
                    hasattr(b_o_p.type, "is_output_array")
                    and not b_o_p.type.is_output_array
                ):
                    b_o_p.type.is_output_array = True
                    heap_allocation_helper(b_o_p)

    @staticmethod
    def get_out_ports_list(nodes):
        retval = []
        for node in nodes:
            if node:
                retval += node.out_ports
        return retval

    def copy_port_values_to_children(self, irbuilder: ll.IRBuilder):
        """Copy values assigned to ports between child nodes.
        ex. if variable was created in init, it must be copied to
        body and reduction, etc.
        """
        # Init's input values are added separately because the class
        # is shared between Loop and Let:
        if self.init:
            copy_port_values(self.in_ports, self.init.in_ports[-len(self.in_ports) :])
            irbuilder.position_at_start(self.entry_start)
            self.init.to_llvm(irbuilder)
            self.entry_end = irbuilder.block

        if self.range_gen:
            copy_port_values(
                self.in_ports, self.range_gen.in_ports[-len(self.in_ports) :]
            )
            self.range_gen.to_llvm(irbuilder)

        if self.body:
            copy_port_values(
                self.get_out_ports_list([self.range_gen, self.init]), self.body.in_ports
            )
            copy_port_values(self.in_ports, self.body.in_ports[-len(self.in_ports) :])
            self.body.to_llvm(irbuilder)

        if self.condition:
            copy_port_values(
                self.in_ports, self.condition.in_ports[-len(self.in_ports) :]
            )
            copy_port_values(
                self.get_out_ports_list([self.body]), self.condition.in_ports
            )
            self.condition.to_llvm(irbuilder)

        copy_port_values(
            self.get_out_ports_list([self.body, self.range_gen, self.init]),
            self.returns.in_ports,
        )

        copy_port_values(self.in_ports, self.returns.in_ports[-len(self.in_ports) :])

    @to_llvm_method
    def to_llvm(self, irbuilder: ll.IRBuilder):
        # create a comment containing names of variables being calculated
        # in the loop:
        result_vars_list = ", ".join(port.label for port in self.out_ports)
        LoopExpression.count += 1
        self.id = LoopExpression.count
        self.reduction_count = 0
        self.last_ret_block = None
        self.predecessor = irbuilder.block
        self.entry_start = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_entry"
        )
        self.entry_end = self.entry_start
        self.header_start = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_header_start"
        )
        self.header_end = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_header_end"
        )
        self.loop_body_start_block = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_body_start"
        )
        self.loop_body_end_block = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_body_end"
        )
        self.latch = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_latch"
        )
        self.follower = irbuilder.append_basic_block(
            name=f"Loop_{LoopExpression.count}_follower"
        )  # ret would be in here
        self.phi_vars = []

        irbuilder.branch(self.entry_start)
        irbuilder.position_at_start(self.entry_start)

        self.copy_port_values_to_children(irbuilder)

        copy_port_labels(self.out_ports, self.returns.out_ports)

        # add a reference to the loop to eachReduction node within Returns node:
        self.returns.copy_loop_object_to_all_reductions(self)

        for o_p, r_o_p in zip(self.out_ports, self.returns.out_ports):
            o_p.value = llvm_eval(r_o_p, irbuilder)
        if not (self.entry_end.is_terminated):
            with irbuilder.goto_block(self.entry_end):
                irbuilder.branch(self.header_start)
        if not (self.latch.is_terminated):
            with irbuilder.goto_block(self.latch):
                irbuilder.branch(self.header_start)
        if self.last_ret_block and not (self.last_ret_block.is_terminated):
            with irbuilder.goto_block(self.last_ret_block):
                irbuilder.branch(self.latch)
        irbuilder.position_at_start(self.follower)


class Body(Node):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        self.name_child_ports()
        irbuilder.position_at_start(self.loop_object.loop_body_start_block)
        for o_p in self.out_ports:
            if o_p.label in [i_p.label for i_p in self.in_ports]:
                # TODO where possible? only with old and initial?
                llvm_eval(o_p, irbuilder)
                self.loop_object.phi_vars += o_p.label
            else:
                llvm_eval(o_p, irbuilder)
            self.loop_object.private_vars += [o_p.value]
        irbuilder.branch(self.loop_object.loop_body_end_block)


class Returns(Node):
    """Returns node. It is assumed that each output port is always connected
    to a Reduction node inside"""

    def copy_loop_object_to_all_reductions(self, loop_object):
        """copy loop to all reduction nodes"""
        for node in self.nodes:
            if type(node) == Reduction:
                node.loop_object = loop_object


class Reduction(Node):
    def mark_heap_allocation(self):
        if (
            isinstance(self.in_ports[1].type, ArrayType)
            and hasattr(self.out_ports[0].type, "is_output_array")
            and self.out_ports[0].type.is_output_array
        ):
            self.in_ports[1].type.is_output_array = True
            source = Edge.edge_to[self.in_ports[1].id].from_
            if source.in_port:
                b_o_p = next(
                    port
                    for port in self.loop_object.body.out_ports
                    if port.label == source.label
                )
                if hasattr(b_o_p.type, "is_output_array"):
                    b_o_p.type.is_output_array = True
                    heap_allocation_helper(b_o_p)
            else:
                heap_allocation_helper(source)

    default_arr_size = 4

    def to_llvm(self, irbuilder: ll.IRBuilder):
        """Reduction node. Receives a boolean (1st port),
        which is a condition for including a new item,
        determined by value (2nd port)"""
        # with goto и header будет в loop func
        redval_init_block = irbuilder.append_basic_block(
            f"Loop_{self.loop_object.id}_reduction_{self.loop_object.reduction_count}_init"
        )
        self.loop_object.reduction_count += 1
        irbuilder.position_at_start(self.loop_object.header_start)
        reduction_value = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
        irbuilder.position_at_start(redval_init_block)
        next_reduction_value = irbuilder.phi(self.out_ports[0].type.errored_llvm_type())
        # currently heap-allocates everything; perhaps, a ggod approach
        if self.operator == "array":
            parent_function = self.get_containing_function()
            with irbuilder.goto_block(self.loop_object.entry_end):
                elemtyp = self.out_ports[0].type.element.errored_llvm_type()

                len = i32(self.default_arr_size)
                if self.loop_object.ranged:
                    # TODO narrow this check to int range with >=1 step!
                    # ranges in sisal include both left and right boundary
                    right_boundary = irbuilder.extract_value(
                        self.loop_object.right_boundary, 1
                    )
                    left_boundary = irbuilder.extract_value(
                        self.loop_object.left_boundary, 1
                    )
                    init_len_minus_one = irbuilder.sub(
                        right_boundary,
                        left_boundary,
                    )
                    # so need to add one to compensate
                    init_len = irbuilder.add(init_len_minus_one, i64(1))
                    len = irbuilder.trunc(init_len, i32)
                size = calc_memsize_at_runtime(irbuilder, elemtyp, len)
                ptr = irbuilder.call(irbuilder.module.malloc, [size])
                parent_function.mallocs.add(ptr)
                if self.out_ports[0].type.is_output_array:
                    parent_function.preserved_mallocs.add(ptr)
                init_reduction_value = ll.Constant(array_descriptor_type, None)
                init_reduction_value = irbuilder.insert_value(
                    init_reduction_value, ptr, 0
                )
                init_reduction_value = irbuilder.insert_value(
                    init_reduction_value,
                    i32zero,
                    1,
                    name="reduction_array",
                )
                errored_init_reduction_value = self.out_ports[0].type.pack_val(
                    init_reduction_value, irbuilder
                )
                reduction_value.add_incoming(
                    errored_init_reduction_value, self.loop_object.entry_end
                )
            irbuilder.position_at_start(self.loop_object.header_start)
            allocated_size = irbuilder.phi(
                i32, f"allocated_size_red_{self.loop_object.reduction_count}"
            )
            allocated_size.add_incoming(len, self.loop_object.entry_end)
        else:
            with irbuilder.goto_block(self.loop_object.entry_end):
                if self.operator == "sum":
                    reduction_value.add_incoming(
                        self.in_ports[1].type.pack_val(
                            ll.Constant(self.in_ports[1].type.llvm_type(), 0), irbuilder
                        ),
                        self.loop_object.entry_end,
                    )
                    self.loop_object.reduction_values += [next_reduction_value]
                    self.loop_object.reduction_operators = ["sis_sum"]
                elif self.operator == "product":
                    reduction_value.add_incoming(
                        self.in_ports[1].type.pack_val(
                            ll.Constant(self.in_ports[1].type.llvm_type(), 1), irbuilder
                        ),
                        self.loop_object.entry_end,
                    )
                    self.loop_object.reduction_values += [next_reduction_value]
                    self.loop_object.reduction_operators = ["sis_product"]
                else:
                    reduction_value.add_incoming(
                        self.in_ports[1].type.pack_val(
                            ll.Constant(self.in_ports[1].type.llvm_type(), 1), irbuilder
                        ),
                        self.loop_object.entry_end,
                    )
        if not self.loop_object.last_ret_block:
            self.loop_object.last_ret_block = self.loop_object.loop_body_end_block
        with irbuilder.goto_block(self.loop_object.last_ret_block):
            input_value = llvm_eval(self.in_ports[1], irbuilder)
            cond = llvm_eval(self.in_ports[0], irbuilder)
            self.loop_object.last_ret_block = irbuilder.block

        then = irbuilder.append_basic_block(
            f"Loop_{self.loop_object.id}_reduction_{self.loop_object.reduction_count}_cond_true"
        )
        otherwise = irbuilder.append_basic_block(
            f"Loop_{self.loop_object.id}_reduction_{self.loop_object.reduction_count}_cond_false"
        )
        err_block = irbuilder.append_basic_block(
            f"Loop_{self.loop_object.id}_reduction_{self.loop_object.reduction_count}_error"
        )
        cond_block = irbuilder.append_basic_block(
            f"Loop_{self.loop_object.id}_reduction_{self.loop_object.reduction_count}_cond_block"
        )
        with irbuilder.goto_block(self.loop_object.last_ret_block):
            reduction_error = irbuilder.extract_value(reduction_value, 0)
            condition_error = irbuilder.extract_value(cond, 0)
            new_val_error = irbuilder.extract_value(input_value, 0)
            errc = irbuilder.or_(reduction_error, condition_error)
            if self.operator != "array":
                errc = irbuilder.or_(errc, new_val_error)

            irbuilder.cbranch(errc, err_block, cond_block)
        with irbuilder.goto_block(cond_block):
            condition_val = irbuilder.extract_value(cond, 1)
            irbuilder.cbranch(condition_val, then, otherwise)
        with irbuilder.goto_block(err_block):
            next_reduction_value.add_incoming(
                self.out_ports[0].type.make_error(irbuilder), err_block
            )
            irbuilder.branch(redval_init_block)

        with irbuilder.goto_block(then):
            if self.operator == "array":
                descriptor = irbuilder.extract_value(reduction_value, 1)
                old_counter = irbuilder.extract_value(descriptor, 1)
                counter = irbuilder.add(
                    old_counter,
                    i32one,
                )
                exceeds = irbuilder.append_basic_block("arr_size_exceeds_allocated")
                not_exceeds = irbuilder.append_basic_block(
                    "arr_size_exceeds_allocated_not"
                )
                new_value = irbuilder.insert_value(descriptor, counter, 1)

                exceeds_check = irbuilder.icmp_unsigned(">", counter, allocated_size)
                irbuilder.cbranch(exceeds_check, exceeds, not_exceeds)
                with irbuilder.goto_block(exceeds):
                    new_size = irbuilder.mul(
                        i32(2), allocated_size
                    )  # doubles allocated size like python does

                    # TODO implement malloc arrays in other cases (via porting from stack to heap after loop?
                    # though i can just call free every time? can i?)
                    new_size_in_bytes = calc_memsize_at_runtime(
                        irbuilder, elemtyp, new_size
                    )

                    new_arr = irbuilder.call(
                        irbuilder.module.realloc, [ptr, new_size_in_bytes]
                    )
                    parent_function.mallocs.remove(ptr)
                    parent_function.mallocs.add(new_arr)
                    if self.out_ports[0].type.is_output_array:
                        parent_function.preserved_mallocs.remove(ptr)
                        parent_function.preserved_mallocs.add(new_arr)
                    new_elem = irbuilder.gep(
                        new_arr,
                        [
                            old_counter,
                        ],
                        source_etype=elemtyp,  # TODO check if correct approach
                    )
                    int_ = irbuilder.ptrtoint(new_elem, i64)
                    new_elem = irbuilder.inttoptr(int_, ll.PointerType())
                    irbuilder.store(input_value, new_elem)
                    new_val_if_exceeds = irbuilder.insert_value(new_value, new_arr, 0)
                    new_val_errored_exceeds = self.out_ports[0].type.pack_val(
                        new_val_if_exceeds, irbuilder
                    )
                    irbuilder.branch(redval_init_block)
                with irbuilder.goto_block(not_exceeds):
                    new_elem = irbuilder.gep(
                        ptr,
                        [
                            old_counter,
                        ],
                        source_etype=elemtyp,  # TODO check if correct approach
                    )
                    int_ = irbuilder.ptrtoint(new_elem, i64)
                    new_elem = irbuilder.inttoptr(int_, ll.PointerType())
                    irbuilder.store(input_value, new_elem)
                    new_value_errored = self.out_ports[0].type.pack_val(
                        new_value, irbuilder
                    )
                    irbuilder.branch(redval_init_block)
                with irbuilder.goto_block(redval_init_block):
                    new_allocated_size = irbuilder.phi(i32)
                    next_reduction_value.add_incoming(new_val_errored_exceeds, exceeds)
                    next_reduction_value.add_incoming(new_value_errored, not_exceeds)
                    new_allocated_size.add_incoming(new_size, exceeds)
                    new_allocated_size.add_incoming(allocated_size, not_exceeds)
                    new_allocated_size.add_incoming(allocated_size, otherwise)
                    new_allocated_size.add_incoming(i32(ll.Undefined), err_block)
                    allocated_size.add_incoming(
                        new_allocated_size, self.loop_object.latch
                    )
            else:
                if self.operator == "value":
                    new_value = input_value
                elif self.operator == "sum":
                    left_operand = irbuilder.extract_value(reduction_value, 1)
                    right_operand = irbuilder.extract_value(input_value, 1)
                    if isinstance(right_operand.type, ll.IntType):
                        new_value = irbuilder.add(
                            left_operand,
                            right_operand,
                        )
                        new_value = self.out_ports[0].type.pack_val(
                            new_value, irbuilder
                        )
                    else:
                        if isinstance(right_operand.type, ll.DoubleType):
                            new_value = irbuilder.fadd(
                                left_operand,
                                right_operand,
                            )
                            new_value = self.out_ports[0].type.pack_val(
                                new_value, irbuilder
                            )
                        else:
                            raise CodeGenError(
                                "Failed to recognize reduction value type"
                            )
                elif self.operator == "product":
                    left_operand = irbuilder.extract_value(reduction_value, 1)
                    right_operand = irbuilder.extract_value(input_value, 1)
                    if isinstance(right_operand.type, ll.IntType):
                        new_value = irbuilder.mul(
                            left_operand,
                            right_operand,
                        )
                        new_value = self.out_ports[0].type.pack_val(
                            new_value, irbuilder
                        )
                    else:
                        if isinstance(right_operand.type, ll.DoubleType):
                            new_value = irbuilder.fmul(
                                left_operand,
                                right_operand,
                            )
                            new_value = self.out_ports[0].type.pack_val(
                                new_value, irbuilder
                            )
                        else:
                            raise CodeGenError(
                                "Failed to recognize reduction value type"
                            )
                next_reduction_value.add_incoming(new_value, then)
                irbuilder.branch(redval_init_block)
            # emit instructions for when the predicate is true
            with irbuilder.goto_block(otherwise):
                new_value = reduction_value
                next_reduction_value.add_incoming(new_value, otherwise)
                irbuilder.branch(redval_init_block)
            reduction_value.add_incoming(next_reduction_value, self.loop_object.latch)
        self.out_ports[0].value = reduction_value
        # resizing after loop; may bring back if the need arises
        """if self.operator == "array" and self.out_ports[0].type.is_output_array:
            with irbuilder.goto_block(self.loop_object.follower):
                old_ptr = irbuilder.extract_value(reduction_value, 0)
                count = irbuilder.extract_value(reduction_value, 1)
                size = calc_memsize_at_runtime(irbuilder, elemtyp, count)
                res = irbuilder.call(irbuilder.module.realloc, [old_ptr, size])
                self.out_ports[0].value = res"""
        self.loop_object.last_ret_block = redval_init_block


class RangeGen(Node):
    """Range generation node."""

    def to_llvm(self, irbuilder: ll.IRBuilder):
        # out ports go like var, var1_index, var2, var2_index, e.t.c.
        self.name_child_ports()
        # copy LoopExpression's input values:
        """for i_p, loop_i_p in zip(
            self.in_ports, self.loop_object.in_ports
        ):  # here it wouldn't be in ports but FUNC ARGS!
            i_p.value = loop_i_p.value"""
        for o_p in self.out_ports:
            # assuming it's always a Scatter Node
            scatter = get_src_node(o_p)
            if type(scatter) != Scatter:
                raise CodeGenError(f"expected scatter node in {self.id}" f"({self})")
            scatter.loop_object = self.loop_object
            llvm_eval(o_p, irbuilder)


class RangeNumeric(Node):

    def to_llvm(self, irbuilder):
        for i_p in self.in_ports:
            llvm_eval(i_p, irbuilder)


class Scatter(Node):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        with irbuilder.goto_block(self.loop_object.entry_end):
            # o_p: element, index
            input_var = llvm_eval(self.in_ports[0], irbuilder)
            self.loop_object.entry_end = irbuilder.block
        input_node = get_src_node(self.in_ports[0])
        if type(input_node) == RangeNumeric:
            with irbuilder.goto_block(self.loop_object.entry_end):
                errored_left = input_node.in_ports[0].value
                errored_right = input_node.in_ports[1].value
                left_error = irbuilder.extract_value(errored_left, 0)
                right_error = irbuilder.extract_value(errored_right, 0)
                self.loop_object.entry_end = irbuilder.block
            with irbuilder.goto_block(self.loop_object.header_start):
                self.out_ports[0].value = irbuilder.phi(
                    input_node.in_ports[0].value.type,
                    name=self.out_ports[0].label,
                )
                self.out_ports[1].value = irbuilder.phi(
                    input_node.in_ports[0].value.type,
                    name=self.out_ports[1].label,
                )
                # prepare error handling
                error_block = irbuilder.append_basic_block(
                    f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_err_block"
                )
                no_error_block = irbuilder.append_basic_block(
                    f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_correct_exec_block"
                )
                with irbuilder.goto_block(self.loop_object.header_end):
                    cond = irbuilder.phi(i1)
                    irbuilder.cbranch(
                        cond,
                        self.loop_object.loop_body_start_block,
                        self.loop_object.follower,
                    )

                with irbuilder.goto_block(error_block):
                    cond.add_incoming(i1(1), error_block)
                    irbuilder.branch(self.loop_object.header_end)
                errcond = irbuilder.or_(left_error, right_error)
                irbuilder.cbranch(errcond, error_block, no_error_block)
                self.loop_object.ranged = True

                # for reduction array heuristics
                self.loop_object.left_boundary = errored_left
                self.loop_object.right_boundary = errored_right

                self.out_ports[0].value.add_incoming(
                    errored_left, self.loop_object.entry_end
                )
                self.out_ports[1].value.add_incoming(  # STUB!
                    errored_left, self.loop_object.entry_end
                )
                with irbuilder.goto_block(self.loop_object.latch):
                    oldval = irbuilder.extract_value(self.out_ports[0].value, 1)
                    element = irbuilder.add(oldval, ll.Constant(i64, 1))
                    element = self.out_ports[0].type.pack_val(element, irbuilder)
                self.out_ports[0].value.add_incoming(element, self.loop_object.latch)
                self.out_ports[1].value.add_incoming(
                    element, self.loop_object.latch
                )  # STUB!
                with irbuilder.goto_block(no_error_block):
                    new_left = irbuilder.extract_value(self.out_ports[0].value, 1)
                    right = irbuilder.extract_value(errored_right, 1)
                    cond.add_incoming(
                        irbuilder.icmp_signed("<=", new_left, right),
                        no_error_block,
                    )
                    irbuilder.branch(self.loop_object.header_end)

        else:
            pass
        # TODO non-int ranges


class Condition(Node):
    """Not used directly (inherited classes are used instead)"""


class PreCondition(Condition):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        irbuilder.position_at_start(self.loop_object.header_start)
        for i_p in self.in_ports:
            if i_p.label in self.loop_object.phi_vars:
                new_value = irbuilder.phi(
                    i_p.type.errored_llvm_type()
                )  # perhaps needs array consideration
                new_value.add_incoming(i_p.value, self.loop_object.entry_end)  # entry
                new_value.add_incoming(
                    next(
                        o_p.value
                        for o_p in self.loop_object.body.out_ports
                        if o_p.label == i_p.label
                    ),
                    self.loop_object.latch,
                )
                i_p.value = new_value

        cond = llvm_eval(self.out_ports[0], irbuilder)
        irbuilder.cbranch(
            cond, self.loop_object.loop_body_start_block, self.loop_object.follower
        )


class PostCondition(Condition):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        irbuilder.position_at_start(self.loop_object.header_start)
        cond = irbuilder.phi(ll.IntType(1))
        cond.add_incoming(
            ll.Constant(ll.IntType(1), 0), self.loop_object.entry_end  # entry
        )

        for i_p in self.in_ports:
            if i_p.label in self.loop_object.phi_vars:
                new_value = irbuilder.phi(
                    i_p.type.errored_llvm_type()
                )  # wtf this even is? consider arrays
                new_value.add_incoming(i_p.value, self.loop_object.entry_end)
                new_value.add_incoming(
                    next(
                        o_p.value
                        for o_p in self.loop_object.body.out_ports
                        if o_p.label == i_p.label
                    ),
                    self.loop_object.latch,
                )
                i_p.value = new_value
        irbuilder.cbranch(
            cond, self.loop_object.loop_body_start_block, self.loop_object.follower
        )
        irbuilder.position_at_start(self.loop_object.latch)
        cond.add_incoming(
            llvm_eval(self.out_ports[0], irbuilder), self.loop_object.latch
        )


class OldValue(Node):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        old_value = llvm_eval(self.in_ports[0], irbuilder)
        # olds_block = CppBlock()
        self.out_ports[0].value = old_value
        # TODO create olds block in LoopExpression object?
