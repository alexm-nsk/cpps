#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type for code generator
"""
import re


class Type:
    def __init__(self, type_object):
        self.location = type_object["location"]
        if "name" in type_object:
            self.name = type_object["name"]
        else:
            self.element = get_type(type_object["element"])
            self.multitype = type_object["multi_type"]

    @property
    def cpp_type(self):
        return f"{self.__cpp_type__}"


class IntegerType(Type):
    __cpp_type__ = "int"

    def load_from_json_code(self, name, src_object):
        return f"{self.cpp_type} {name} = {src_object}.asInt();"

    def save_to_json_code(self, target_object, object_):
        return f"{target_object} = {object_};"


class RealType(Type):
    __cpp_type__ = "float"

    def load_from_json_code(self, name, src_object):
        return f"{self.cpp_type} {name} = {src_object}.asFloat();"

    def save_to_json_code(self, target_object, object_):
        return f"{target_object} = {object_};"


class BooleanType(Type):
    __cpp_type__ = "bool"

    def load_from_json_code(self, name, src_object):
        return f"{self.cpp_type} {name} = {src_object}.asBool();"

    def save_to_json_code(self, target_object, object_):
        return f"{target_object} = {object_};"


def remove_spec_symbols(string):
    return re.sub("[^a-zA-Z0-9]", "_", string)


class ArrayType(Type):
    @property
    def cpp_type(self):
        return f"vector<{self.element.cpp_type}>"

    def dimensions(self):
        return (1 +
                (self.element.dimensions if "element" in self.element.__dict__
                 else 0))

    def load_from_json_code(self, name, src_object):
        from .cpp.cpp_codegen import indent_cpp
        index_name = "index_for_" + remove_spec_symbols(name)
        item_name = "item_for_" + remove_spec_symbols(name)
        retval = (f"{self.cpp_type} {name};\n"
                  f'for(unsigned int {index_name} = 0;\n'
                  f'index < {src_object}.size();\n++{index_name})\n''{\n' +
                  indent_cpp(
                      self.element.load_from_json_code(item_name,
                                                       (f"{src_object}"
                                                        f"[{index_name}]")) +
                      f'\n{name}.push_back({item_name});') +
                  '\n}')

        return retval

    def save_to_json_code(self, target_object, object_):
        from .cpp.cpp_codegen import indent_cpp
        index = "index_for_" + remove_spec_symbols(target_object)
        item_name = "item_for_" + remove_spec_symbols(target_object)

        return (
                f"for(unsigned int {index} = 0;\n"
                f"    {index} < size({object_});"
                f"\n    ++{index})"
                "\n{\n" +
                indent_cpp(f"{self.element.cpp_type} {item_name};") +
                "\n" +
                indent_cpp(self.element.save_to_json_code(item_name,
                                                          object_ +
                                                          f"[{index}]")) +
                "\n" +
                indent_cpp(f"{target_object}.append({item_name});") +
                "\n}"
                )


class StreamType(Type):

    @property
    def cpp_type(self):
        return f"vector<{self.element.cpp_type}>"


class AnyType(Type):
    pass


type_map = {
    "integer": IntegerType,
    "real": RealType,
    "boolean": BooleanType,
    "array": ArrayType,
    "stream": StreamType,
    "any": AnyType,
}


def get_type(type_data: dict):
    if "name" in type_data:
        if type_data["name"] in type_map:
            return type_map[type_data["name"]](type_data)
        else:
            raise Exception(f"type {type_data['name']} is not supported")
    elif "element" in type_data:
        if "multi_type" in type_data:
            if type_data["multi_type"].lower() == "stream":
                return StreamType(type_data)
        return ArrayType(type_data)
