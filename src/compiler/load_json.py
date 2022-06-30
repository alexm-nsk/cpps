#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""Deserializes json IRs"""

import json
import re

json_re = re.compile("[a-z]([A-Z])")
re_remove_ = re.compile("_(?=$)")


def load_json(file_name: str):
    with open(file_name, "r") as json_file:
        contents = json.loads(json_file.read())
        return contents
