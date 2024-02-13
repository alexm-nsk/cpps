import re

json_re = re.compile("_([a-z])")
re_remove_ = re.compile("_(?=$)")


def python_names(obj, fields=False):
    """Converts camelCase to snake_case in a dictionary
    fields is signalling that this sub dictionary is from a user defined
    type and we must leave the keys (names of *fields* unchanged)
    """
    new_object = {}

    def convert(value, fields=False):
        if isinstance(value, dict):
            return python_names(value, fields)
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    for key, value in obj.items():
        new_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower() if not fields else key
        new_object[new_key] = convert(value, key=="fields")

    return new_object


def json_names(obj):
    """Converts snake_case to camelCase in a dictionary
    and removes '_' at the end"""
    new_object = {}

    def convert(value):
        if isinstance(value, dict):
            return json_names(value)
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    for key, value in obj.items():
        new_key = re.sub(json_re, lambda m: m.group(1).upper(), key)
        new_key = re.sub(re_remove_, "", new_key)
        new_object[new_key] = convert(value)

    return new_object
