#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import os
import json
import subprocess
import threading
from multiprocessing import Pool


EXAMPLES_PATH = "../examples/"


def get_example_files_list():
    files = []

    for (path, _, filenames) in os.walk(EXAMPLES_PATH):
        for f in filenames:
            module_name = os.path.splitext(f)[0]
            module_input_data_name = path + "io_data/" + module_name + ".json"

            if os.path.isfile(module_input_data_name) and f.endswith(".sis"):
                files += [
                    (
                        path + f,
                        module_input_data_name,
                        module_name,
                    )
                ]

    print(f"{len(files)} test program{'s' * (len(files)!=1)} found.")
    return files


def compile_cpp(src_code, module_name):
    cmd_line = f"g++ -xc++ - -fopenmp -fconcepts -ljsoncpp -Wall -o {module_name} -O3".split()
    proc = subprocess.Popen(
        cmd_line,
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        shell=False,
    )

    def writer():
        proc.stdin.write(bytes(src_code, "utf-8"))
        proc.stdin.close()

    thread = threading.Thread(target=writer)
    thread.start()
    thread.join()
    proc.wait()


def run_cpp(input_data, module_name):
    cmd_line = f"./{module_name}"

    proc = subprocess.Popen(
        cmd_line, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=False
    )
    output = []

    def writer(program_output):
        proc.stdin.write(bytes(input_data, "utf-8"))
        proc.stdin.close()

        program_output += [proc.stdout.read().decode()]

    thread = threading.Thread(target=writer, args=[output])
    thread.start()
    thread.join()
    proc.wait()

    return output[0]


def process_module(file_name, input_file, module_name):
    # print(f"parsing {file_name}...")
    try:
        result = subprocess.run(
            ["python", "sisal.py", "-i", file_name, "--cpp"], stdout=subprocess.PIPE
        )
        cpp_module = result.stdout.decode("utf-8")
    except Exception as e:
        print("internal error:", str(e))
        return

    compile_cpp(cpp_module, module_name)

    if os.path.isfile(module_name):
        input_data_object = json.load(open(input_file, "r"))
        # num_tests = len(input_data_object["inputs"])
        test_number = 1

        for test_data in input_data_object:
            program_input = test_data["input"]
            expected_program_output = test_data["output"]
            # program_output = json.loads(output)
            program_output = json.loads(run_cpp(json.dumps(program_input), module_name))
            expected_output = expected_program_output

            if program_output == expected_output:
                print(
                    f"\033[92mTest#{test_number}"
                    f" for {file_name} passed.\033[0m"
                )
            else:
                print(f"\033[91mTest for {module_name} failed.\033[0m")
                print(f"expected output: {expected_output}," f" got: {program_output}")

            test_number += 1

        os.system("rm " + module_name)
    else:
        print(f"\033[91mTest for {module_name} failed: C++ code didn't compile.\033[0m")
        return


def main(args):
    with Pool() as pool:
        pool.starmap(process_module, get_example_files_list())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
