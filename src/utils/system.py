#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

'''Various functions for OS interaction'''

import sys


def get_piped_input():
    """Checks if IR is provided via pipe"""
    input_text = ""
    input_text = "".join(sys.stdin)
    return input_text
