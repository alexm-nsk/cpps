import sys

sys.path.append("..")

from ir.module import Module
from ir.ast_.literal import Literal
from ir.edge import Edge
from ir.type import IntegerType


def codegen(module):
    print ("new codegen requested")
    print(module.functions)
    pass
