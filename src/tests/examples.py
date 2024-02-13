#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import os
import json
import subprocess


EXAMPLES_PATH = "../examples/"
EXAMPLES_PATH = "../../projects/sisal-cl/examples/elementary/"


def get_example_files_list():
    files = []
    for (path, _, filenames) in os.walk(EXAMPLES_PATH):
        files += [path + f for f in filenames if f.endswith(".sis")]
    print(f"{len(files)} test programs found.")
    return files


def main(args):

    for file_name in get_example_files_list():
        print(f"parsing {file_name}...")
        try:
            result = subprocess.run(
                ["python", "sisal.py", "-i", file_name, "--json"],
                stdout=subprocess.PIPE
            )
        except Exception as e:
            print("internal error:", str(e))
            break

        result_data = json.loads(result.stdout.decode("utf-8"))
        if "errors" in result_data:
            print("\033[91m", result_data["errors"], "\033[0m")
        else:
            print("\033[92mOK!\033[0m")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
