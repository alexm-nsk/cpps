#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Describes an Error class for code generator
"""


# TODO make internal error (ex. for 'Number of output ports requested, b...)'"

class CodeGenError(Exception):
    def __init__(self, message: str, location: str = None):
        super().__init__(message)
        self.location = f"({location})" if location else ""

    def __str__(self):
        return f"Code Generation Error {self.location}: " + super().__str__()
