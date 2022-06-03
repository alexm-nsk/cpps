#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Describes an Error class
"""


class SisalError(Exception):
    def __init__(self, message: str, location: str = ""):
        super().__init__(message)
        self.location = location

    def __str__(self):
        return f"Sisal Error ({self.location}): " + super().__str__()

    pass


class SisalSyntaxError(SisalError):
    pass


class TypeMismatch(SisalError):
    pass
