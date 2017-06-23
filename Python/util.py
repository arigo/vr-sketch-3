import math


class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def tolist(self):
        return [self.x, self.y, self.z]

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scale):
        if isinstance(scale, Vector3):
            raise TypeError("can't multiply two vectors")
        return Vector3(self.x * scale, self.y * scale, self.z * scale)

    def __div__(self, inverse_scale):
        if isinstance(inverse_scale, Vector3):
            raise TypeError("can't divide two vectors")
        return self * (1.0 / inverse_scale)
    
    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
