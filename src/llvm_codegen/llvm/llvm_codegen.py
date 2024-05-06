import llvmlite.ir as ll
import llvmlite.binding as llvm
from ..edge import Edge
from ..error import CodeGenError


# где-то здесь будет определение модуля, вероятно, классом с методом, который будет его инициализировать
class LlModule(ll.Module):
    def __init__(self, name: str, functions: dict, definitions: dict = {}):
        super().__init__(name)
        self.builder = ll.IRBuilder(None)
        self.engine = None
        self.modref = None
        self.inputs = []
        self.output = None
        self.printf = ll.Function(
            self,
            ll.FunctionType(ll.IntType(32), [ll.PointerType()], var_arg=True),
            name="printf",
        )
        self.malloc = ll.Function(
            self,
            ll.FunctionType(ll.PointerType(), [ll.IntType(64)]),
            name="malloc",
        )
        self.calloc = ll.Function(
            self,
            ll.FunctionType(ll.PointerType(), [ll.IntType(64)]),
            name="calloc",
        )
        self.realloc = ll.Function(
            self,
            ll.FunctionType(ll.PointerType(), [ll.PointerType(), ll.IntType(64)]),
            name="realloc",
        )
        self.memcpy = ll.Function(
            self,
            ll.FunctionType(
                ll.VoidType(),
                [ll.PointerType(), ll.PointerType(), ll.IntType(64), ll.IntType(1)],
            ),
            name="llvm.memcpy.p0.p0.i64",
        )
        self.sizeof = ll.Function(
            self,
            ll.FunctionType(
                ll.IntType(64), [ll.PointerType(), ll.PointerType(), ll.IntType(64)]
            ),
            name="sizeof",
        )
        self.int_power = ll.Function(
            self,
            ll.FunctionType(ll.IntType(64), [ll.IntType(64), ll.IntType(64)]),
            name="llvm.powi.i64",
        )
        self.double_power = ll.Function(
            self,
            ll.FunctionType(ll.DoubleType(), [ll.DoubleType(), ll.DoubleType()]),
            name="llvm.pow.f64",
        )
        self.free = ll.Function(
            self,
            ll.FunctionType(ll.VoidType(), [ll.PointerType()]),
            name="free",
        )
        self.array_print_loop_count = 0
        for _, f in functions.items():
            f.module = self
            # self.add_global(
            f.to_llvm(self.builder)  #
        from ..ast_.function import create_main

        create_main(self.builder)

    def __str__(self):
        return super().__str__()

    def set_inputs(self, types: dict):
        self.inputs = types

    def get_input_types(self):
        return self.inputs.values()

    def get_input_ctypes(self, args: list):
        # from ctypes import POINTER
        from ..type import ArrayType, RecordType

        if len(args) != len(self.inputs.values()):
            raise CodeGenError("Number of arguments doesn't match")

        return [
            _type.ctype if type(_type) is not ArrayType else type(_type.to_ctype(arg))
            for _type, arg in zip(self.inputs.values(), args)
        ]

    def get_input_names(self):
        return self.inputs.keys()

    def set_output(self, types):
        if len(types) > 0:
            self.output = types

    def get_output_ctype(self):
        if self.output:
            from ..type import RecordType, ArrayType

            if len(self.output.items()) != 1:
                ctypes = [
                    (
                        (name, _type.ctype)
                        if type(_type) != ArrayType
                        else (name, _type.make_retval())
                    )
                    for name, _type in self.output.items()
                ]
                return RecordType.make_ctypes_struct(fields=ctypes[:])
            else:
                out = list(self.output.items())[0][1]
                outctype = out.ctype if type(out) != ArrayType else out.make_retval()
                return outctype
        else:
            from ctypes import c_int

            return c_int

    @staticmethod
    def optimize(module, target_machine, speed_level=2, size_level=2):
        pto = llvm.create_pipeline_tuning_options(
            speed_level=speed_level if speed_level else 2,
            size_level=size_level if size_level else 2,
        )  # speed: 0-3, size:0-2
        pto.loop_vectorization = True
        pto.slp_vectorization = True
        pto.loop_unrolling = True
        # Create the pass builder
        pass_builder = llvm.create_pass_builder(target_machine, pto)

        # Get a populated module pass manager
        mpm = pass_builder.getModulePassManager()
        mpm.add_instruction_combine_pass()
        mpm.add_simplify_cfg_pass()

        mpm.run(module, pass_builder)

    def preprocess_ir(self, target_triple=None, speed_level=None, size_level=None):
        module = llvm.parse_assembly(str(self))
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        if not target_triple:
            target = llvm.Target.from_default_triple()
        else:
            target = llvm.Target.from_triple(target_triple)
        target_machine = target.create_target_machine()
        engine = llvm.create_mcjit_compiler(module, target_machine)
        engine.finalize_object()
        engine.run_static_constructors()
        self.engine = engine
        self.modref = module
        return module, target_machine

    def print_optimized(self, target_triple=None, speed_level=None, size_level=None):
        module, target_machine = self.preprocess_ir(target_triple)
        self.optimize(module, target_machine, speed_level, size_level)
        return str(module)

    def bitcode_gen(self, target_triple=None, speed_level=None, size_level=None):
        module, target_machine = self.preprocess_ir(target_triple)
        self.optimize(module, target_machine, speed_level, size_level)
        return module.as_bitcode()

    def make_cfunc(self, args: list, speed_level=None, size_level=None):
        from ctypes import CFUNCTYPE, _Pointer, Structure, Array

        def process_output(res):
            if isinstance(res, _Pointer):
                print("res inst ptr")
                res = res.contents
            if issubclass(type(res), Structure):
                ret = "{\n"
                for field in res._fields_:
                    ret += f"{field[0]}: {process_output(getattr(res,field[0]))}\n"
                ret += "}\n"
                return ret
            if isinstance(res, Array):
                ret = f"[{res[0]}"
                for i in range(1, res._length_):
                    ret += f", {process_output(res[i])}"
                ret += "]\n"
                return ret
            return res

        if not self.engine:
            self.bitcode_gen(speed_level=speed_level, size_level=size_level)
        func_ptr = self.engine.get_function_address("main")
        out_ = self.get_output_ctype()
        # out_is_array = self.out_is_array()
        inp = self.get_input_ctypes(args)
        cfunctup = CFUNCTYPE(out_, *inp)
        cfunc = cfunctup(func_ptr)
        args_formatted = []
        for arg, argtype in zip(args, self.get_input_types()):
            arg_formatted = argtype.to_ctype(arg)
            args_formatted.append(arg_formatted)
        return cfunc, args_formatted

    def run_on_jit(self, args: list, speed_level=None, size_level=None):
        cfunc, args_formatted = self.make_cfunc(args, speed_level, size_level)
        res = cfunc(*args_formatted)
        return res

    def measure_runtime(
        self, args: list, speed_level=None, size_level=None, repeats=1000
    ):
        cfunc, args_formatted = self.make_cfunc(args, speed_level, size_level)

        def timer():
            return cfunc(*args_formatted)

        import timeit

        time = timeit.timeit(timer, globals=globals(), number=repeats)
        return f"Total time for {repeats} executions: {time:.6f} seconds\nAverage per execution: {time/repeats:.10f} seconds"


class BranchCount:
    count = 0


def llvm_eval(in_port, irbuilder):
    port = Edge.edge_to[in_port.id].from_
    if port.value is None:
        port.node.to_llvm(irbuilder)
    in_port.value = port.value
    return port.value


def heap_allocation_helper(in_port):
    port = Edge.edge_to[in_port.id].from_
    from ..type import ArrayType

    if isinstance(in_port.type, ArrayType):
        if in_port.type.is_output_array:
            port.type.is_output_array = True
            if not port.in_port:
                port.node.mark_heap_allocation()
