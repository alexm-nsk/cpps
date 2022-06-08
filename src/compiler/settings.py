"""various global parameters are stored here"""
# if a port's label is None, don't store it when exporting an IR
DONT_ADD_EMPTY_LABELS = True
# don't use separate node for Let and
# turn it into a simple set of nodes and edges
UNPACK_LET = False
