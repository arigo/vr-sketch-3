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

    def cross(self, other):
        return Vector3(self.y * other.z - self.z * other.y,
                       self.z * other.x - self.x * other.z,
                       self.x * other.y - self.y * other.x)

    def normalized(self):
        return self * (1.0 / abs(self))

    def withcoord(self, coord_name, newvalue):
        v = Vector3(self.x, self.y, self.z)
        setattr(v, coord_name, newvalue)
        return v


class Plane(object):
    def __init__(self, normal, distance):
        self.normal = normal
        self.distance = distance

    @staticmethod
    def from_vertices(vertices):
        # _approx_plane() is injected in this module's globals by App.__init__()
        lst = []
        for v in vertices:
            lst += v.tolist()
        result = _approx_plane(lst)
        return Plane(Vector3(result[0], result[1], result[2]), result[3])

    def distance_to_point(self, pt):
        return self.normal.dot(pt) + self.distance