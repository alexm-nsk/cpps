#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Describes sisal types"""
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class Type:
    """describes a Sisal type"""

    location: str = "not applicable"

    def __eq__(self, obj):
        return type(self) == type(obj)
        return False

    def ir_(self):
        """An IR form of the type"""
        retval = self.__dict__
        return retval

    def is_array(self):
        return hasattr(self, "element")

    def is_stream(self):
        return type(self) == StreamType

    def get_a_copy(self, location: str = "not applicable"):
        copy = deepcopy(self)
        copy.location = location
        return copy

    def gml(self):
        return self.name


@dataclass
class AnyType(Type):
    """Class for describing arbitrary type"""

    name: str = "any"

    def gml(self):
        return "any type"


@dataclass
class IntegerType(Type):
    """Class for describing integer type"""

    name: str = "integer"

    def gml(self):
        return "integer"


@dataclass
class BooleanType(Type):
    """Class for describing boolean type"""

    name: str = "boolean"

    def gml(self):
        return "boolean"


@dataclass
class RealType(Type):
    """Class for describing real types"""

    name: str = "real"

    def gml(self):
        return "real"


@dataclass
class MultiType(Type):
    """Class for describing arrays, streams, etc."""

    element: Type = None

    @property
    def name(self):
        # TODO make sure it's always processed
        if "name" in self.element.__dict__:
            return self.element

    def gml(self):
        return "multi_type"


@dataclass
class StreamType(MultiType):
    """Class for describing streams."""

    def ir_(self):
        retval = deepcopy(self.__dict__)["element"].ir_()
        # TODO mark it explicitly as stream somehow
        retval["location"] = self.location
        retval["multi_type"] = "stream"
        return retval

    def element_type(self):
        return self.element

    def gml(self):
        return f"stream of {self.element.gml()}"


@dataclass
class ArrayType(MultiType):
    """Class for describing arrays."""

    def __eq__(self, obj):
        if "element" not in obj.__dict__:
            return False
        return self.element == obj.element

    def ir_(self):
        retval = deepcopy(self.__dict__)
        retval["element"] = retval["element"].ir_()
        retval["multi_type"] = "array"
        return retval

    def depth(self):
        if self.element.is_array():
            return 1 + self.element.depth()
        else:
            return 1

    def element_type(self):
        return self.element

    def bottom_element_type(self):
        """returns the type of single element of an array"""
        return (
            self.element.bottom_element_type()
            if self.element.is_array()
            else self.element
        )

    def gml(self):
        return f"array of {self.element.gml()}"


@dataclass
class RecordType(Type):
    fields: dict = None  # name, type

    name: str = "record"

    def __eq__(self, obj):
        if "fields" not in obj.__dict__:
            return False
        return self.fields == obj.fields

    def ir_(self):
        fields = deepcopy(self.fields)
        fields = {k: v.ir_() for k, v in fields.items()}
        return dict(name="record",
                    location=self.location,
                    fields=fields)


class TypeDefinition:
    def __init__(self, name: str, type_: Type):
        self.name = name
        self.type = type_
        self.type.custom_type = True
        self.type.type_name = name

    def ir_(self):
        return dict(name=self.name, type=self.type.ir_())
