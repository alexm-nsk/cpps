#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""Deserializes json IRs"""

import json
from utils.python_names import python_names


def load_json(file_data: str):
    contents = json.loads(file_data)
    return python_names(contents)
