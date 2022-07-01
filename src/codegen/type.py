#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type for code generator
"""


class Type:
    def __init__(self, type_object):
        self.location = type_object["location"]
        if "name" in type_object:
            self.name = type_object["name"]
        else:
            self.element = get_type(type_object["element"])
            self.multitype = type_object["multi_type"]


class IntegerType:
    pass


class RealType:
    pass


class BooleanType:
    pass


class ArrayType:
    pass


class StreamType:
    pass


type_map = {
    "Integer": IntegerType,
    "Real": RealType,
    "Boolean": BooleanType,
    "Array": ArrayType,
    "Stream": StreamType,
}


def get_type(type_data: dict):

    if hasattr(type_data, "name"):
        if hasattr(type_map, type_data["name"]):
            return type_map[type_data["name"]](type_data)
        else:
            raise Exception(f"type {type_data['name']} is not supported")
    elif hasattr(type_data, "element"):
        if hasattr(type_data, "multi_type"):
            if type_data["multi_type"].lower() == "array":
                return StreamType(type_data)
        return ArrayType(type_data)
