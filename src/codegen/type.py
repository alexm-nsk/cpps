#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type for code generator
"""
import re
import json
from .codegen_state import global_no_error
"""Type classes have load_from_json_code and save_to_json_code
 methods. They return C++ code for those corresponding purposes
"""


class Type:
    def __init__(self, type_object):
        self.location = type_object["location"]
        for extra_field in ["type_name", "custom_type"]:
            if extra_field in type_object:
                self.__dict__[extra_field] = type_object[extra_field]

        if "fields" in type_object:
            self.fields = {}
            for field, type_ in type_object["fields"].items():
                self.fields[field] = get_type(type_)

        if "name" in type_object:
            self.name = type_object["name"]
        else:
            self.element = get_type(type_object["element"])
            self.multi_type = type_object["multi_type"]

    @property
    def cpp_type(self):
        if "custom_type" in self.__dict__ and self.custom_type:
            return self.type_name
        else:
            return f"{self.__cpp_type__}"

    @property
    def internal_type(self):
        return self.__cpp_type__

    def save_to_json_code(self, target_object, object_):
        if global_no_error:
            return f'{target_object} = {object_};'
        else:
            return f'if ({object_}.error) {target_object} = "ERROR"; else {target_object} = {object_};'


class IntegerType(Type):
    __cpp_type__ = "int" if global_no_error else "integer"

    def load_from_json_code(self, name, src_object):
        return f"{self.cpp_type} {name} = {src_object}.asInt();"


class RealType(Type):
    __cpp_type__ = "float" if global_no_error else "real"

    def load_from_json_code(self, name, src_object):
        return f"{self.cpp_type} {name} = {src_object}.asFloat();"


class BooleanType(Type):
    __cpp_type__ = "boolean" if global_no_error else "bool"

    def load_from_json_code(self, name, src_object):
        return f"{self.cpp_type} {name} = {src_object}.asBool();"


def remove_spec_symbols(string):
    return re.sub("[^a-zA-Z0-9]", "_", string).replace(".", "_")


class ArrayType(Type):
    @property
    def __cpp_type__(self):
        if global_no_error:
            return f"std::vector<{self.element.cpp_type}>"
        else:
            return f"Array<{self.element.cpp_type}>"

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

    def load_from_json_code(self, name, src_object):
        from .cpp.cpp_codegen import indent_cpp

        index_name = "index_for_" + remove_spec_symbols(name)
        item_name = "item_for_" + remove_spec_symbols(name)
        retval = (
            f"{self.cpp_type} {name};\n"
            f"for(unsigned int {index_name} = 0;\n"
            f"{index_name} < {src_object}.size();\n++{index_name})\n"
            "{\n"
            + indent_cpp(
                self.element.load_from_json_code(
                    item_name, (f"{src_object}" f"[{index_name}]")
                )
                + f"\n{name}.push_back({item_name});"
            )
            + "\n}"
        )

        return retval

    def save_to_json_code(self, target_object, object_):
        from .cpp.cpp_codegen import indent_cpp

        index = "index_for_" + remove_spec_symbols(target_object)
        item_name = "item_for_" + remove_spec_symbols(target_object)

        return (
            (f"if ({object_}.error)"
             "{\n"
             + indent_cpp(f'{target_object}="ERROR";') +
             "\n}\nelse\n") * (not global_no_error) +
            f"for(unsigned int {index} = 0;\n"
            f"    {index} < size({object_});"
            f"\n    ++{index})"
            "\n{\n"
            + indent_cpp(f"Json::Value {item_name};")
            + "\n"
            + indent_cpp(
                self.element.save_to_json_code(item_name, object_ + f"[{index}]")
            )
            + "\n"
            + indent_cpp(f"{target_object}.append({item_name});")
            + "\n}"
        )


class StreamType(Type):
    @property
    def cpp_type(self):
        if "custom_type" in self.__dict__ and self.custom_type:
            return self.type_name
        else:
            return f"vector<{self.element.cpp_type}>"


class AnyType(Type):
    @property
    def cpp_type(self):
        return "auto"


def get_struct_string(name: str, fields: list[str]):
    from .cpp.cpp_codegen import indent_cpp

    set_error_code = (
        "\nvoid set_error(){\n"
        + ";\n".join([str(field) + ".set_error()" for field, _ in fields.items()])
        + ";\n}"
    )
    extra = ("bool error;" + set_error_code) * (not global_no_error)
    field_defs = "\n".join(
        [f"{str(type_.cpp_type)} {str(field)};" for field, type_ in fields.items()]
    )
    return "struct " + name + "{\n" + indent_cpp(field_defs + "\n" + extra) + "\n};"


class RecordType(Type):
    @property
    def __cpp_type__(self):
        return self.cpp_type

    @property
    def cpp_type(self):
        return self.get_struct()["name"]

    # static, contains description of corresponding C++
    # structs as strings
    cpp_structs = {}

    def get_struct(self):
        """returns a C++ struct based on this record"""

        if hash(self) not in RecordType.cpp_structs:
            name = "record" + str(len(RecordType.cpp_structs))
            struct_str = get_struct_string(name, self.fields)
            RecordType.cpp_structs[hash(self)] = dict(name=name, string=struct_str)
        return RecordType.cpp_structs[hash(self)]

    def __hash__(self):
        return hash(
            json.dumps(
                {type_.cpp_type: name for name, type_ in self.fields.items()},
                sort_keys=True,
            )
        )

    # declare struct and put it on the list
    # use it as type
    def load_from_json_code(self, name, src_object):
        ret_str = "\n".join(
            [
                type_.load_from_json_code(
                    name + f"_{field}", src_object + f'["{field}"]'
                )
                for field, type_ in self.fields.items()
            ]
        )
        ret_str += "\n" + self.get_struct()["name"] + " " + name + ";"
        ret_str += "\n" + "\n".join(
            [
                f"{name}.{field} = {name}_{field};"
                for field, type_ in self.fields.items()
            ]
        )

        return ret_str

    def save_to_json_code(self, target_object, object_):
        return "\n".join(
            [
                type_.save_to_json_code(
                    target_object + f'["{field}"]', object_ + f".{field}"
                )
                for field, type_ in self.fields.items()
            ]
        )


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
            return type_map[type_data["name"]](type_data)
        else:
            raise Exception(f"type {type_data['name']} is not supported")
    elif "element" in type_data:
        if "multi_type" in type_data:
            if type_data["multi_type"].lower() == "stream":
                return StreamType(type_data)
        return ArrayType(type_data)


def get_integer():
    """helper for creating indices"""
    return IntegerType({"name": "integer", "location": "not applicable"})
