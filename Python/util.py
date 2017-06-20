class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def tolist(self):
        return [self.x, self.y, self.z]

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

