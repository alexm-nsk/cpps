#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Describes syntax rules
"""

rule_annotations = {
    "def": "function definition or function import",
    "bin_op": "binary operation (do you have an empty expression?)",
    "module": "function, comment, or pragma"
}


def rule_annotation(rule_name: str):
    if rule_name in rule_annotations:
        return rule_annotations[rule_name]
    else:
        return rule_name
