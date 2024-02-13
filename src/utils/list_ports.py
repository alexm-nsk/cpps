#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""Lists ports in specified node, or all nodes"""


from system import get_piped_input
import json
import sys
from python_names import python_names


INDENT = "  "


def print_port_data(port):
    print(
        INDENT,
        f'{port["index"]}:' f'{port["label"] if "label" in port else "(no label)"}',
    )


def list_ports(node, name=None, id=None):

    if "name" in node or "id" in node:
        if node["name"] == name or node["id"] == id:
            print()
            print(f'{node["name"]} ({node["id"]})')
            if "in_ports" in node:
                print("Input ports:")
                for i_p in node["in_ports"]:
                    print_port_data(i_p)
            if "out_ports" in node:
                print("Output ports:")
                for o_p in node["out_ports"]:
                    print_port_data(o_p)

        for key, value in node.items():
            if type(value) == dict:
                list_ports(value, name, id)
            elif type(value) == list:
                for node in value:
                    list_ports(node, name, id)


def get_names_and_ids(args):

    names = []
    ids = []
    for index, arg in enumerate(args):
        if arg == "--name":
            for input_name in args[index + 1:]:
                if not input_name.startswith("--"):
                    names.append(input_name)
                else:
                    break

        if arg == "--id":
            for input_id in args[index + 1:]:
                if not input_id.startswith("--"):
                    ids.append(input_id)
                else:
                    break

    return names, ids


def main(args):

    # receive input from pipe:
    ir_json = get_piped_input()
    try:
        ir = python_names(json.loads(ir_json))
    except Exception as e:
        print("Error decoding IR data:", str(e))
        return

    # get names and ids into lists:
    try:
        names, ids = get_names_and_ids(args)

    except Exception as e:
        description = ""
        if type(e) == IndexError:
            description = "no name provided after argument type"
        print(f"Malformed command line ({description}).")
        return

    # list port using names and ids:
    try:
        print(names, ids)
        for function in ir["functions"]:
            for name in names:
                list_ports(function, name)
            for id in ids:
                list_ports(function, id=id)
    except Exception as e:
        print("Error traversing IR data or incorrect IR data", str(e))
        return


if __name__ == "__main__":
    sys.exit(main(sys.argv))
