

class BranchDescription:

    def __init__(self, angle, name):
        self.angle = angle
        self.name = name

    def __str__(self):
        return "%s : %s" % (self.name, self.angle)

    def __repr__(self):
        return self.__str__()