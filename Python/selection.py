from worldobj import Cylinder, SmallSphere, PolygonHighlight
from util import Vector3, SinglePoint, WholeSpace, Plane, Line


DISTANCE_VERTEX_MIN = SinglePoint._SELECTION_DISTANCE
DISTANCE_EDGE_MIN = Line._SELECTION_DISTANCE
DISTANCE_FACE_MIN = Plane._SELECTION_DISTANCE

class HoverColorScheme:
    VERTEX = 0x80FFFF
    EDGE   = 0x00D0D0
    VOID   = 0x00A0A0
    FACE   = 0x80FFFF

class SelectedColorScheme:
    VERTEX = 0xFF4040
    EDGE   = 0xD00000
    VOID   = 0xA00000
    FACE   = 0xFF40FF

class TargetColorScheme:
    VERTEX = 0x80FF80
    EDGE   = 0x00D000
    VOID   = 0x00A000
    FACE   = 0x80FF80

class GuideColorScheme:
    EDGE   = 0xC0C0C0


class SelectVertex(object):
    def __init__(self, app, vertex):
        self.app = app
        self.vertex = vertex

    def flash(self, color_scheme):
        self.app.flash(SmallSphere(self.vertex.position, color_scheme.VERTEX))

    def get_point(self):
        return self.vertex.position

    def get_subspace(self):
        return SinglePoint(self.vertex.position)

    def adjust(self, pt):
        pass

    def alignment_guides(self):
        return _all_45degree_guides(self.vertex.position)


def _all_45degree_guides(position):
    for axis in _ALL_45DEGREE_AXES:
        yield Line(position, axis)
    yield Plane.from_point_and_normal(position, Vector3(1, 0, 0))
    yield Plane.from_point_and_normal(position, Vector3(0, 1, 0))
    yield Plane.from_point_and_normal(position, Vector3(0, 0, 1))

_ALL_45DEGREE_AXES = [
    Vector3(1, 0, 0),
    Vector3(0, 1, 0),
    Vector3(0, 0, 1),
    Vector3(1, 1, 0).normalized(),
    Vector3(1, 0, 1).normalized(),
    Vector3(0, 1, 1).normalized(),
    Vector3(1, -1, 0).normalized(),
    Vector3(1, 0, -1).normalized(),
    Vector3(0, 1, -1).normalized()]


class SelectAlongEdge(object):
    def __init__(self, app, edge, fraction):
        self.app = app
        self.edge = edge
        self.fraction = fraction    # maybe rounded to exactly 0.5, for the middle

    def flash(self, color_scheme):
        p1 = self.edge.v1.position
        p2 = self.edge.v2.position
        #self.app.flash(Cylinder(p1, p2, color_scheme.EDGE))
        color = color_scheme.EDGE if self.fraction != 0.5 else color_scheme.VERTEX
        self.app.flash(SmallSphere(p1 + (p2 - p1) * self.fraction, color))

    def get_point(self):
        p1 = self.edge.v1.position
        p2 = self.edge.v2.position
        return p1 + (p2 - p1) * self.fraction

    def get_subspace(self):
        if self.fraction == 0.5:
            return SinglePoint(self.get_point())
        p1 = self.edge.v1.position
        p2 = self.edge.v2.position
        return Line(p1, (p2 - p1).normalized())

    def adjust(self, pt):
        if self.fraction != 0.5:
            p1 = self.edge.v1.position
            p2 = self.edge.v2.position
            diff = p2 - p1
            self.fraction = diff.dot(pt - p1) / diff.dot(diff)

    def alignment_guides(self):
        p1 = self.edge.v1.position
        p2 = self.edge.v2.position
        yield Line(p1, (p2 - p1).normalized())
        if self.fraction == 0.5:
            p = (p1 + p2) * 0.5
            yield Plane.from_point_and_normal(p, (p2 - p1).normalized())
            for guide in _all_45degree_guides(p):
                yield guide


class SelectOnFace(object):
    def __init__(self, app, face, position):
        self.app = app
        self.face = face
        self.position = position

    def flash(self, color_scheme):
        self.app.flash(PolygonHighlight([edge.v1.position for edge in self.face.edges], color_scheme.FACE))
        self.app.flash(SmallSphere(self.position, color_scheme.FACE))

    def get_point(self):
        return self.position

    def get_subspace(self):
        return self.face.plane

    def adjust(self, pt):
        self.position = self.face.plane.project_point_inside(pt)

    def alignment_guides(self):
        yield self.face.plane


class SelectVoid(object):
    def __init__(self, app, position):
        self.app = app
        self.position = position

    def flash(self, color_scheme):
        self.app.flash(SmallSphere(self.position, color_scheme.VOID))

    def get_point(self):
        return self.position

    def get_subspace(self):
        return WholeSpace()

    def adjust(self, pt):
        self.position = pt

    def alignment_guides(self):
        return []


def find_closest(app, position):
    for attempt in [find_closest_vertex, find_closest_edge, find_closest_face, SelectVoid]:
        result = attempt(app, position)
        if result is not None:
            return result
    raise AssertionError("unreachable")

def find_closest_vertex(app, position):
    closest = None
    distance_min = app.scale_ctrl(DISTANCE_VERTEX_MIN)
    for v in app.model.all_vertices():
        distance = abs(position - v.position)
        if distance < distance_min:
            distance_min = distance * 1.01
            closest = SelectVertex(app, v)
    return closest

def find_closest_edge(app, position):
    closest = None
    distance_min = app.scale_ctrl(DISTANCE_EDGE_MIN)
    for e in app.model.edges:
        frac, distance = e.measure_distance(position)
        if 0 < frac < 1 and distance < distance_min:
            distance_min = distance * 1.01
            if abs(position - (e.v1.position + e.v2.position) * 0.5) < app.scale_ctrl(DISTANCE_VERTEX_MIN):
                frac = 0.5
            closest = SelectAlongEdge(app, e, frac)
    return closest

def find_closest_face(app, position):
    closest = None
    distance_min = app.scale_ctrl(DISTANCE_FACE_MIN)
    for face in app.model.faces:
        signed_distance = face.plane.signed_distance_to_point(position)
        distance = abs(signed_distance)
        if distance < distance_min and face.point_is_inside(position):
            distance_min = distance * 1.01
            closest = SelectOnFace(app, face, position - face.plane.normal * signed_distance)
    return closest
