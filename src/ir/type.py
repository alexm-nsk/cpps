#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type for code generator
"""
import re
from copy import deepcopy


class Type:

    @classmethod
    def load_from_data(cls, type_object):
        self = cls()
        self.location = type_object["location"]
        for extra_field in ["type_name", "custom_type"]:
            if extra_field in type_object:
                self.__dict__[extra_field] = type_object[extra_field]

        if "fields" in type_object:
            self.fields = {}
            for field, type_ in type_object["fields"].items():
                self.fields[field] = get_type(type_)

        if "name" in type_object:
            self.name = cls.name
        else:
            self.element = get_type(type_object["element"])
            self.multi_type = type_object["multi_type"]

        return self

    def ir_(self):
        """An IR form of the type"""
        retval = self.__dict__
        return retval

    def __init__(self):
        if hasattr(self, "name"):
            self.name = self.name
        self.location = ""


class IntegerType(Type):
    convert=int
    name = "integer"


class RealType(Type):
    convert=float
    name = "real"


class BooleanType(Type):
    convert=bool
    name="boolean"
    pass


def remove_spec_symbols(string):
    return re.sub("[^a-zA-Z0-9]", "_", string).replace(".", "_")


class ArrayType(Type):
    def dimensions(self):
        return 1 + (
            self.element.dimensions if "element" in self.element.__dict__ else 0
        )

    def bottom_element_type(self):
        """returns the type of single element of an array"""
        return (
            self.element.bottom_element_type()
            if type(self.element) == ArrayType
            else self.element
        )

    def ir_(self):
        retval = deepcopy(self.__dict__)
        retval["element"] = retval["element"].ir_()
        # retval["multi_type"] = "array"
        return retval


class StreamType(Type):
    pass


class AnyType(Type):
    name = "any"
    pass


class RecordType(Type):
    name = "record"
    pass


type_map = {
    "integer": IntegerType,
    "real": RealType,
    "boolean": BooleanType,
    "array": ArrayType,
    "stream": StreamType,
    "any": AnyType,
    "record": RecordType,
}


def get_type(type_data: dict):
    if "name" in type_data:
        if type_data["name"] in type_map:
            return type_map[type_data["name"]].load_from_data(type_data)
        else:
            raise Exception(f"type {type_data['name']} is not supported")
    elif "element" in type_data:
        if "multi_type" in type_data:
            if type_data["multi_type"].lower() == "stream":
                return StreamType.load_from_data(type_data)
        return ArrayType.load_from_data(type_data)
