"""various global parameters are stored here"""
# if a port's label is None, don't store it when exporting an IR
DONT_ADD_EMPTY_LABELS = True

# don't use separate node for Let and
# turn it into a simple set of nodes and edges
UNPACK_LET = False

# When exporting IR as JSON, copy full description of ports
# (sisal-cl compatibility)
PORT_FULL_DESCRIPTION_IN_EDGES = False

# replace strings like "<" and ">" with strings like "&lt" and "&gt"
REPLACE_XML_TAGS = True
