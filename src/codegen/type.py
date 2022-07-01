

class Type:
    def __init__(self, type_object):
        self.location = type_object["location"]
        if "name" in type_object:
            self.name = type_object["name"]
        else:
            self.element = Type(type_object["element"])
            self.multitype = type_object["multi_type"]

