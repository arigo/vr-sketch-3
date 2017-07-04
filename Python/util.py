import math

EPSILON = 1e-5


class Vector3(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'Vector3(%s, %s, %s)' % (self.x, self.y, self.z)

    def tolist(self):
        return [self.x, self.y, self.z]

    @staticmethod
    def from_axis(axis_name, norm=1.):
        if axis_name == "x":
            return Vector3(norm, 0., 0.)
        elif axis_name == "y":
            return Vector3(0., norm, 0.)
        elif axis_name == "z":
            return Vector3(0., 0., norm)
        else:
            raise ValueError(axis_name)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scale):
        if isinstance(scale, Vector3):
            raise TypeError("can't multiply two vectors")
        return Vector3(self.x * scale, self.y * scale, self.z * scale)
    __rmul__ = __mul__

    def __div__(self, inverse_scale):
        if isinstance(inverse_scale, Vector3):
            raise TypeError("can't divide two vectors")
        return self * (1.0 / inverse_scale)

    def __pos__(self):
        return self

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)
    
    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Vector3):
            return NotImplemented
        return abs(self - other) < EPSILON

    def __ne__(self, other):
        if self is other:
            return False
        if not isinstance(other, Vector3):
            return NotImplemented
        return abs(self - other) >= EPSILON

    def __hash__(self):
        raise TypeError("cannot hash Vector3")

    def exactly_equal(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

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

    def closest_axis_plane(self, minimum):
        dx = abs(self.x)
        dy = abs(self.y)
        dz = abs(self.z)
        if dx <= min(dy, dz, minimum):
            return "x"
        elif dy <= min(dx, dz, minimum):
            return "y"
        elif dz <= min(dx, dy, minimum):
            return "z"
        else:
            return None

    def project_orthogonal(self, normal):
        return self - normal * normal.dot(self) / float(normal.dot(normal))


class AffineSubspace(object):
    """Base class for affine subspaces of the space."""

    def distance_to_point(self, pt):
        # default implementation
        return abs(pt - self.project_point_inside(pt))

    def selection_distance(self, app, pt):
        # Compute distance_to_point(pt), but scaled in such a way that results > 1
        # are considered too far to be selected.  Returns (family, scaled_distance)
        # where 'family' is the dimensionality.  This allows results to be ordered.
        d = app.scale_ctrl(self.distance_to_point(pt)) / self._SELECTION_DISTANCE
        return (self._DIMENSIONALITY, d)


class EmptyIntersection(Exception):
    pass


class WholeSpace(AffineSubspace):
    _SELECTION_DISTANCE = 1
    _DIMENSIONALITY = 3

    def project_point_inside(self, pt):
        return pt

    def distance_to_point(self, pt):
        return 0.0

    def intersect(self, subspace):
        return subspace

    def shifted(self, delta):
        return self


class Plane(AffineSubspace):
    _SELECTION_DISTANCE = 0.04
    _DIMENSIONALITY = 2

    def __init__(self, normal, distance):
        # NOTE: 'normal' is supposed to be normalized
        self.normal = normal
        self.distance = distance

    @staticmethod
    def from_vertices(vertices):
        # _approx_plane() is injected in this module's globals by app.initialize_functions()
        lst = []
        for v in vertices:
            lst += v.tolist()
        result = _approx_plane(lst)
        return Plane(Vector3(result[0], result[1], result[2]), result[3])

    @staticmethod
    def from_point_and_normal(from_point, normal):
        return Plane(normal, -normal.dot(from_point))

    def very_close_to_plane(self, other):
        if self.normal == other.normal:
            return abs(self.distance - other.distance) < EPSILON
        elif self.normal == -other.normal:
            return abs(self.distance + other.distance) < EPSILON
        else:
            return False

    def signed_distance_to_point(self, pt):
        return self.normal.dot(pt) + self.distance

    def distance_to_point(self, pt):
        return abs(self.signed_distance_to_point(pt))

    def project_point_inside(self, pt):
        return pt - self.normal * self.signed_distance_to_point(pt)

    def intersect(self, subspace):
        if not isinstance(subspace, Plane):
            return subspace.intersect(self)
        normal1 = self.normal.cross(subspace.normal)
        d = abs(normal1)
        selfpt = self.normal * (-self.distance)
        if d < EPSILON:
            if subspace.distance_to_point(selfpt) < EPSILON:
                return self
            else:
                raise EmptyIntersection
        else:
            normal1 /= d
            in_line = self.normal.cross(normal1)
            d1 = subspace.signed_distance_to_point(selfpt)
            d2 = subspace.signed_distance_to_point(selfpt + in_line)
            f = d1 / float(d1 - d2)
            pt = selfpt + f * in_line
            return Line(pt, normal1)

    def shifted(self, delta):
        return Plane(self.normal, self.distance - self.normal.dot(delta))


class Line(AffineSubspace):
    _SELECTION_DISTANCE = 0.044
    _DIMENSIONALITY = 1

    def __init__(self, from_point, axis):
        # NOTE: 'axis' is supposed to be normalized
        self.from_point = from_point
        self.axis = axis

    def project_point_inside(self, pt):
        fraction = self.axis.dot(pt - self.from_point)
        return self.from_point + self.axis * fraction

    def intersect(self, subspace):
        if isinstance(subspace, (SinglePoint, WholeSpace)):
            return subspace.intersect(self)
        #
        # if two points on the line 'self' are also almost in 'subspace', then
        # the intersection will be the whole line 'self'
        if (subspace.distance_to_point(self.from_point) < EPSILON and
            subspace.distance_to_point(self.from_point + self.axis) < EPSILON):
            return self
        #
        # otherwise, the intersection is at most one point
        if isinstance(subspace, Line):
            v = (self.from_point - subspace.from_point).project_orthogonal(subspace.axis)
            d1 = v.dot(v)
            d2 = v.dot(v + self.axis)
        elif isinstance(subspace, Plane):
            d1 = subspace.signed_distance_to_point(self.from_point)
            d2 = subspace.signed_distance_to_point(self.from_point + self.axis)
        else:
            raise AssertionError

        if abs(d1 - d2) < EPSILON:
            raise EmptyIntersection
        f = d1 / float(d1 - d2)
        pt = self.from_point + f * self.axis
        if subspace.distance_to_point(pt) > EPSILON:
            raise EmptyIntersection
        return SinglePoint(pt)

    def shifted(self, delta):
        return Line(self.from_point + delta, self.axis)


class SinglePoint(AffineSubspace):
    _SELECTION_DISTANCE = 0.05
    _DIMENSIONALITY = 0

    def __init__(self, position):
        self.position = position

    def project_point_inside(self, pt):
        return self.position

    def intersect(self, subspace):
        if subspace.distance_to_point(self.position) > EPSILON:
            raise EmptyIntersection
        return self

    def shifted(self, delta):
        return SinglePoint(self.position + delta)