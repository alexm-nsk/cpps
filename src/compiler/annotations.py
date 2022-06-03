rule_annotations = {
    "def": "function definition or function import",
    "bin_op": "binary operation",
}


def rule_annotation(rule_name: str):
    if rule_name in rule_annotations:
        return rule_annotations[rule_name]
    else:
        return rule_name
