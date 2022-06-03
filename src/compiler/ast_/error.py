#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
Describes an Error class
"""


class SisalError(Exception):
    pass


class SisalSyntaxError(SisalError):
    pass


class TypeMismatch(SisalError):
    pass
