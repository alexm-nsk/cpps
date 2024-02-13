import os
from string import Template
templates = {}


def load_template(file_name):
    if file_name not in templates:
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + "/templates/" + file_name, "r") as f:
            templates[file_name] = Template(f.read().strip())
    return templates[file_name]
