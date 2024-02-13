#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code generator if
"""
from ..node import Node, to_cpp_method
from ..cpp.cpp_codegen import CppVariable, indent_cpp, CppBlock, cpp_eval, CppAssignment


class If(Node):

    name = "if"
    copy_parent_input_values = True

    @to_cpp_method
    def to_cpp(self, block):

        if_results = []

        for index, o_p in enumerate(self.out_ports):
            if_result = CppVariable(o_p.label,
                                    self.out_ports[index].type.cpp_type)
            if_results.append(if_result)
            block.add_variable(if_result)
            o_p.value = if_result

        # create cpp blocks for conditions and branches:
        cond_blocks = ([block] +
                       [CppBlock(False, False)
                        for i in range(len(self.branches) - 1)])
        else_if_blocks = [CppBlock(True, True)
                          for i in range(len(self.branches) - 1)]

        condition_results = self.condition.to_cpp(self, cond_blocks)

        then_block = CppBlock()
        else_block = CppBlock()

        # evaluate branches:

        for o_p in self.out_ports:
            self.branches[0].to_cpp(self, o_p, then_block)
            for index, (branch, branch_block) in enumerate(
                zip(self.branches[1:-1], else_if_blocks[:-1])
            ):
                branch.to_cpp(self, o_p, branch_block)
            self.branches[-1].to_cpp(self, o_p, else_block)

        # make the resulting string:

        elseifs = ""
        for elseif_block, cond_result in zip(else_if_blocks,
                                             condition_results[1:]):
            elseifs += f"\nelse if({cond_result})\n{str(elseif_block)}"

        block.add_code(
            f"if({condition_results[0]})"
            "\n{\n"
            f"{indent_cpp(str(then_block))}"
            "\n}" + elseifs + "\nelse\n"
            "{\n"
            f"{indent_cpp(str(else_block))}"
            "\n}"
        )


class Branch(Node):
    def to_cpp(self, parent_if, result_port, block):
        for i_p, p_ip in zip(self.in_ports, parent_if.in_ports):
            i_p.value = p_ip.value
        block.add_code(
            CppAssignment(
                result_port.value, cpp_eval(self.out_ports[result_port.index],
                                            block)
            )
        )


class Condition(Node):
    def to_cpp(self, parent_if, blocks):
        name = "if_test"

        condition_results = []

        for i_p, p_ip in zip(self.in_ports, parent_if.in_ports):
            i_p.value = p_ip.value

        for o_p, block in zip(self.out_ports, blocks):
            cond_result = CppVariable(name, "bool")
            blocks[0].add_variable(cond_result)
            blocks[0].add_code(CppAssignment(cond_result,
                                             cpp_eval(o_p, blocks[0])))
            condition_results.append(cond_result)

        return condition_results
