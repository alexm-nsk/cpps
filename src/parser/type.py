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

    name: str = "Any"

    def gml(self):
        return "any type"


@dataclass
class SingularType(Type):
    """Class for describing singular sisal types
    (integer, real, boolean etc.)"""

    name: str = None

    def gml(self):
        return "singular type"


@dataclass
class IntegerType(Type):
    """Class for describing integer type"""

    name: str = "Integer"

    def gml(self):
        return "integer"


@dataclass
class BooleanType(Type):
    """Class for describing boolean type"""

    name: str = "Boolean"

    def gml(self):
        return "boolean"


@dataclass
class RealType(Type):
    """Class for describing real types"""

    name: str = "Real"

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
