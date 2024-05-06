import sys
from ..node import Node
from ..port import Port
from ..edge import Edge
from ..llvm.llvm_codegen import llvm_eval
from ..llvm.llvmlite_helpers import i1
import llvmlite.ir as ll


class Binary(Node):
    def to_llvm(self, irbuilder: ll.IRBuilder):

        int_operator_map = {
            "+": lambda x, y, label="": irbuilder.add(x, y, name=label),
            "-": lambda x, y, label="": irbuilder.sub(x, y, name=label),
            "*": lambda x, y, label="": irbuilder.mul(x, y, name=label),
            "/": lambda x, y, label="": irbuilder.sdiv(x, y, name=label),
            ">": lambda x, y, label="": irbuilder.icmp_signed(">", x, y, name=label),
            "<": lambda x, y, label="": irbuilder.icmp_signed("<", x, y, name=label),
            "=": lambda x, y, label="": irbuilder.icmp_signed("==", x, y, name=label),
            "~=": lambda x, y, label="": irbuilder.icmp_signed("!=", x, y, name=label),
            ">=": lambda x, y, label="": irbuilder.icmp_signed(">=", x, y, name=label),
            "<=": lambda x, y, label="": irbuilder.icmp_signed("<=", x, y, name=label),
            "&": lambda x, y, label="": irbuilder.and_(x, y, name=label),
            "|": lambda x, y, label="": irbuilder.or_(x, y, name=label),
            "**": lambda x, pow, label="": irbuilder.call(
                irbuilder.module.int_power, [x, pow], name=label
            ),
        }
        float_operator_map = {
            "+": lambda x, y, label="": irbuilder.fadd(x, y, name=label),
            "-": lambda x, y, label="": irbuilder.fsub(x, y, name=label),
            "*": lambda x, y, label="": irbuilder.fmul(x, y, name=label),
            "/": lambda x, y, label="": irbuilder.fdiv(x, y, name=label),
            ">": lambda x, y, label="": irbuilder.fcmp_unordered(">", x, y, name=label),
            "<": lambda x, y, label="": irbuilder.fcmp_unordered("<", x, y, name=label),
            "=": lambda x, y, label="": irbuilder.fcmp_unordered("=", x, y, name=label),
            "~=": lambda x, y, label="": irbuilder.fcmp_unordered(
                "!=", x, y, name=label
            ),
            ">=": lambda x, y, label="": irbuilder.fcmp_unordered(
                ">=", x, y, name=label
            ),
            "<=": lambda x, y, label="": irbuilder.fcmp_unordered(
                "<=", x, y, name=label
            ),
            "**": lambda x, pow, label="": irbuilder.call(
                irbuilder.module.double_power, [x, pow], name=label
            ),
        }
        errored_left = llvm_eval(self.in_ports[0], irbuilder)
        errored_right = llvm_eval(self.in_ports[1], irbuilder)
        errcond_left = irbuilder.extract_value(errored_left, 0)
        left = irbuilder.extract_value(errored_left, 1)
        errcond_right = irbuilder.extract_value(errored_right, 0)
        right = irbuilder.extract_value(errored_right, 1)
        operator = self.operator
        isintl = isinstance(left.type, ll.IntType)
        isintr = isinstance(right.type, ll.IntType)

        if self.out_ports[0].label:
            label = self.out_ports[0].label
        else:
            label = ""

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
        with irbuilder.goto_block(error_block):
            irbuilder.branch(phi_block)

        # error handling; prev errcond set during llvm_eval
        errcond = irbuilder.or_(errcond_left, errcond_right)
        if self.operator == "/":
            zero_division = (
                irbuilder.icmp_signed("==", right, right.type(0))
                if isintr
                else irbuilder.fcmp_unordered("==", right, right.type(0))
            )
            errcond = irbuilder.or_(errcond, zero_division)
            # TODO check if both are allowed types (parser shouldnt allow that tho)
        irbuilder.cbranch(
            errcond,
            error_block,
            no_error_block,
        )
        irbuilder.position_at_start(no_error_block)
        if isintl and isintr:
            res = int_operator_map[operator](left, right, label)
        else:
            if isintl:
                left = irbuilder.sitofp(left, typ=ll.DoubleType())
            if isintr:
                right = irbuilder.sitofp(right, ll.DoubleType)
            isfl = (isinstance(left.type, ll.FloatType)) | (
                isinstance(left.type, ll.DoubleType)
            )
            isfr = (isinstance(right.type, ll.FloatType)) | (
                isinstance(right.type, ll.DoubleType)
            )
            if isfl and isfr:
                res = float_operator_map[operator](left, right, label)
        # finish error handling
        irbuilder.branch(phi_block)
        irbuilder.position_at_start(phi_block)
        o_p = self.out_ports[0]
        errored_ret_type = (
            o_p.type.errored_llvm_type()
            if self.operator != "~="
            else ll.LiteralStructType([i1, i1])
        )
        phi = irbuilder.phi(o_p.type.llvm_type() if self.operator != "~=" else i1)
        phi.add_incoming(phi.type(ll.Undefined), error_block)
        phi.add_incoming(res, no_error_block)
        ret = errored_ret_type(None)
        ret = irbuilder.insert_value(ret, errcond, 0)
        ret = irbuilder.insert_value(ret, phi, 1)
        o_p.value = ret


class Unary(Node):

    def to_llvm(self, irbuilder: ll.IRBuilder):
        int_operator_map = {
            "+": lambda x, label="": irbuilder.add(
                ll.Constant(ll.IntType(64), 0), x, name=label
            ),  # затычка в целом после редукций identity не должно возникать
            "-": lambda x, label="": irbuilder.neg(x, name=label),  # целочисленное
            "!": lambda x, label="": irbuilder.not_(x, name=label),
        }

        float_operator_map = {
            "+": lambda x, label="": irbuilder.fadd(
                ll.Constant(type(x), 0), x, name=label
            ),  # затычка
            "-": lambda x, label="": irbuilder.fneg(x, name=label),  # целочисленное
        }
        errored_operand = llvm_eval(self.in_ports[0], irbuilder)
        operator = self.operator
        # prepare error handling
        errcond = irbuilder.extract_value(errored_operand, 0)
        operand = irbuilder.extract_value(errored_operand, 1)
        error_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_err_block"
        )
        no_error_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_correct_exec_block"
        )
        phi_block = irbuilder.append_basic_block(
            f"{self.name if hasattr(self,'name') else self.__class__.__name__ }_phi_block"
        )
        with irbuilder.goto_block(error_block):
            irbuilder.branch(phi_block)

        # error handling
        irbuilder.cbranch(
            errcond,
            error_block,
            no_error_block,
        )
        irbuilder.position_at_start(no_error_block)

        if isinstance(operand.type, ll.IntType):
            res = int_operator_map[operator](operand)
        else:
            if (isinstance(operand.type, ll.FloatType)) | (
                isinstance(operand.type, ll.DoubleType)
            ):
                res = float_operator_map[operator](operand)
        # finish error handling
        irbuilder.branch(phi_block)
        irbuilder.position_at_start(phi_block)
        o_p = self.out_ports[0]
        errtyp = o_p.type.errored_llvm_type()
        phi = irbuilder.phi(o_p.type.llvm_type())
        phi.add_incoming(phi.type(ll.Undefined), error_block)
        phi.add_incoming(res, no_error_block)
        ret = errtyp(None)
        ret = irbuilder.insert_value(ret, errcond, 0)
        ret = irbuilder.insert_value(ret, phi, 1)
        o_p.value = ret
