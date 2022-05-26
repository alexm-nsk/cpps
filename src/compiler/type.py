#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Describes sisal types"""
#from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Type:
    """describes a Sisal type"""

    location: str = "not applicable"

    def __eq__(self, obj):
        print("IMPLEMENT AN _EQ FOR TYPE!!!")
        return False

    def ir_(self):
        """An IR form of the type"""
        retval = self.__dict__
        return retval


@dataclass
class SingularType(Type):
    """Class for describing singular sisal types
    (integer, real, boolean etc.)"""

    name: str = None


@dataclass
class IntegerType(Type):
    """Class for describing singular sisal types
    (integer, real, boolean etc.)"""

    name: str = "Integer"


@dataclass
class BooleanType(Type):
    """Class for describing singular sisal types
    (integer, real, boolean etc.)"""

    name: str = "Boolean"


@dataclass
class RealType(Type):
    """Class for describing singular sisal types
    (integer, real, boolean etc.)"""

    name: str = "Real"


@dataclass
class MultiType(Type):
    """Class for describing arrays, streams, etc."""

    element: Type = None
