#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""Deserializes json IRs"""

import json
import re


def python_names(obj):
    """Converts snake_case to camelCase in a dictionary
    and removes '_' at the end"""
    new_object = {}

    def convert(value):
        if isinstance(value, dict):
            return python_names(value)
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    for key, value in obj.items():
        new_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
        new_object[new_key] = convert(value)

    return new_object


def load_json(file_data: str):
    contents = json.loads(file_data)
    return python_names(contents)
