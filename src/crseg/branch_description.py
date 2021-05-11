
from . import utils as u

class BranchDescription:

    def __init__(self, angle, name):
        self.angle = angle
        self.name = name

    def is_similar(self, bd, angle_similarity = 90):
        if self.name == None or bd.name == None:
            return False
        if self.name != bd.name:
            return False

        if u.Util.angular_distance(self.angle, bd.angle) < angle_similarity:
            return True

        return False

    def is_orthogonal(self, angle, epsilon = 45):
        diff = u.Util.angular_distance(self.angle, angle)
        if diff >= 90 - epsilon and diff <= 90 + epsilon:
            return True
        return False

    def __str__(self):
        return "%s : %s" % (self.name, self.angle)

    def __repr__(self):
        return self.__str__()