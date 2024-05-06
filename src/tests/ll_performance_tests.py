import sys
import os
import json
import subprocess
import contextlib

EXAMPLES_PATH = "examples/"
# EXAMPLES_PATH = "../../projects/sisal-cl/examples/elementary/"


def get_example_files_list():
    files = []

    for path, _, filenames in os.walk(EXAMPLES_PATH):
        for f in filenames:
            module_name = os.path.splitext(f)[0]
            module_input_data_name = path + "io_data/" + module_name + ".json"

            if os.path.isfile(module_input_data_name) and f.endswith(".sis"):
                files += [
                    (
                        path + f,
                        module_name,
                        module_input_data_name,
                    )
                ]

    print(f"{len(files)} test program{'s' * (len(files)!=1)} found.")
    return files


def process_module(file_name, module_name, input_file):
    report_file = open(f"llvm_ir_listings/{module_name}_report.txt", "w")
    print(f"{module_name} report:\n", file=report_file)
    try:
        result = subprocess.run(
            [
                "python3",
                "src/sisal.py",
                "-i",
                file_name,
                "--llvm",
                "--print-raw",
            ],
            stdout=subprocess.PIPE,
        )
        ll_module_string = result.stdout.decode("utf-8")
        if ll_module_string == "":
            print(f"failed to generate ir for {file_name}\n", file=report_file)
            return
        ll_output = open(f"llvm_ir_listings/{module_name}_raw.ll", "w")
        print(ll_module_string, file=ll_output)
    except Exception as e:
        print(f"internal error:{str(e)}\n", file=report_file)
        return
    input_data_object = json.load(open(input_file, "r"))
    inputs = json.dumps(input_data_object[0]["input"]).replace("'", '"')
    for i in range(0, 4):
        for j in range(0, 3):
            try:
                result = subprocess.run(
                    [
                        "python3",
                        "src/sisal.py",
                        "-i",
                        file_name,
                        "--llvm",
                        "--print-optimized",
                        "--speed-level",
                        str(i),
                        "--size-level",
                        str(j),
                    ],
                    stdout=subprocess.PIPE,
                )
                ll_module_string = result.stdout.decode("utf-8")
                if ll_module_string == "":
                    print(
                        f"failed to optimize ir for {file_name} with speed={i} size={j}\n",
                        file=report_file,
                    )
                    if i == j == 0:
                        return
                    continue
                ll_output = open(
                    f"llvm_ir_listings/{module_name}_sp_{i}_size_{j}.ll", "w"
                )
                print(ll_module_string, file=ll_output)
                result = subprocess.run(
                    [
                        "python3",
                        "src/sisal.py",
                        "-i",
                        file_name,
                        "--llvm",
                        "--llvmlitejit",
                        "--speed-level",
                        str(i),
                        "--size-level",
                        str(j),
                    ],
                    input=json.dumps(inputs),
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                )
                try:
                    output = result.stdout.decode("utf-8")
                except:
                    output = result.stdout
                if output == "":
                    continue
                print(
                    f"{module_name} with speed={i} and size={j}:{output.replace("args as JSON:",'')};\nExpected output: {input_data_object[0]["output"]}",
                    file=report_file,
                )
                print("\n")
                result = subprocess.run(
                    [
                        "python3",
                        "src/sisal.py",
                        "-i",
                        file_name,
                        "--llvm",
                        "--measure-runtime",
                        "--repeats",
                        str(5),
                        "--speed-level",
                        str(i),
                        "--size-level",
                        str(j),
                    ],
                    input=json.dumps(inputs),
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                )
                try:
                    output = result.stdout.decode("utf-8")
                except:
                    output = result.stdout
                if output == "":
                    continue
                print(
                    f"runtime measurement {module_name} with speed={i} and size={j}:{output.replace("args as JSON:",'')};\n",
                    file=report_file,
                )
                print("\n")
            except Exception as e:
                print(f"internal error:{str(e)}\n", file=report_file)


def main(args):
    examples = get_example_files_list()
    for example in examples:
        process_module(*example)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
