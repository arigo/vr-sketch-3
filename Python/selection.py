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

class BluishHoverColorScheme:
    VERTEX = 0x80C0FF
    EDGE   = 0x009CD0
    VOID   = 0x0078A0
    FACE   = 0x80C0FF

class SelectedColorScheme:
    VERTEX = 0xFF4040
    EDGE   = 0xD00000
    VOID   = 0xA00000
    FACE   = 0xFF40FF
    EDGE_AXIS = {'x': 0xD00000, 'y': 0x00D000, 'z': 0x0000D0}

class TargetColorScheme:
    VERTEX = 0x80FF80
    EDGE   = 0x00D000
    VOID   = 0x00A000
    FACE   = 0x80FF80
    DARKER_EDGE = 0x00A000

ADD_COLOR = 0x40FF40
SELECTED_COLOR = 0xC070CF
DELETE_COLOR = 0xFF364B


class SelectVertex(object):
    def __init__(self, app, position):
        self.app = app
        self.position = position

    def flash(self, color_scheme):
        self.app.flash(SmallSphere(self.position, color_scheme.VERTEX))

    def flash_flat(self, color):
        pass

    def get_point(self):
        return self.position

    def get_subspace(self):
        return SinglePoint(self.position)

    def adjust(self, pt):
        pass

    def alignment_guides(self):
        return all_45degree_guides(self.position)

    def individual_vertices(self):
        return [self.position]

    def individual_edges(self):
        return []


def all_45degree_guides(position):
    for col1, col2, axis in _ALL_45DEGREE_AXES:
        yield col1, col2, Line(position, axis)
    yield 0x00D0D0, 0x00D0D0, Plane.from_point_and_normal(position, Vector3(1, 0, 0))
    yield 0xD000D0, 0xD000D0, Plane.from_point_and_normal(position, Vector3(0, 1, 0))
    yield 0xD0D000, 0xD0D000, Plane.from_point_and_normal(position, Vector3(0, 0, 1))

_ALL_45DEGREE_AXES = [
    (0xE00000, 0xE00000, Vector3(1, 0, 0)),
    (0x00E000, 0x00E000, Vector3(0, 1, 0)),
    (0x0000E0, 0x0000E0, Vector3(0, 0, 1)),
    (0xE00000, 0x00E000, Vector3(1, 1, 0).normalized()),
    (0xE00000, 0x0000E0, Vector3(1, 0, 1).normalized()),
    (0x00E000, 0x0000E0, Vector3(0, 1, 1).normalized()),
    (0xE00000, 0x00E000, Vector3(1, -1, 0).normalized()),
    (0xE00000, 0x0000E0, Vector3(1, 0, -1).normalized()),
    (0x00E000, 0x0000E0, Vector3(0, 1, -1).normalized()),
    ]


class SelectAlongEdge(object):
    def __init__(self, app, edge, fraction):
        self.app = app
        self.edge = edge
        self.fraction = fraction    # maybe rounded to exactly 0.5, for the middle

    def flash(self, color_scheme):
        p1 = self.edge.v1
        p2 = self.edge.v2
        color = color_scheme.EDGE if self.fraction != 0.5 else color_scheme.VERTEX
        self.app.flash(SmallSphere(p1 + (p2 - p1) * self.fraction, color))

    def flash_flat(self, color):
        self.app.flash(Cylinder(self.edge.v1, self.edge.v2, color))

    def get_point(self):
        p1 = self.edge.v1
        p2 = self.edge.v2
        return p1 + (p2 - p1) * self.fraction

    def get_subspace(self):
        if self.fraction == 0.5:
            return SinglePoint(self.get_point())
        p1 = self.edge.v1
        p2 = self.edge.v2
        return Line(p1, (p2 - p1).normalized())

    def adjust(self, pt):
        if self.fraction != 0.5:
            p1 = self.edge.v1
            p2 = self.edge.v2
            diff = p2 - p1
            self.fraction = diff.dot(pt - p1) / diff.dot(diff)

    def alignment_guides(self):
        p1 = self.edge.v1
        p2 = self.edge.v2
        yield 0xC0C0C0, 0xC0C0C0, Line(p1, (p2 - p1).normalized())
        if self.fraction == 0.5:
            p = (p1 + p2) * 0.5
            yield 0xC0C0C0, 0xC0C0C0, Plane.from_point_and_normal(p, (p2 - p1).normalized())
            for guide in all_45degree_guides(p):
                yield guide

    def individual_vertices(self):
        return [self.edge.v1, self.edge.v2]

    def individual_edges(self):
        return [self.edge]


class SelectOnFace(object):
    def __init__(self, app, face, position):
        self.app = app
        self.face = face
        self.position = position

    def flash(self, color_scheme):
        self.app.flash(PolygonHighlight([edge.v1 for edge in self.face.edges], color_scheme.FACE))
        self.app.flash(SmallSphere(self.position, color_scheme.FACE))

    def flash_flat(self, color):
        # xxx use ColoredPolygon with a shader to fix the overlap issue?
        self.app.flash(PolygonHighlight([edge.v1 for edge in self.face.edges], color))

    def get_point(self):
        return self.position

    def get_subspace(self):
        return self.face.plane

    def adjust(self, pt):
        self.position = self.face.plane.project_point_inside(pt)

    def alignment_guides(self):
        yield 0xB0B0B0, 0xC0C0C0, self.face.plane

    def individual_vertices(self):
        return [edge.v1 for edge in self.face.edges]

    def individual_edges(self):
        return self.face.edges


class SelectVoid(object):
    def __init__(self, app, position):
        self.app = app
        self.position = position

    def flash(self, color_scheme):
        self.app.flash(SmallSphere(self.position, color_scheme.VOID))

    def flash_flat(self, color):
        pass

    def get_point(self):
        return self.position

    def get_subspace(self):
        return WholeSpace()

    def adjust(self, pt):
        self.position = pt

    def alignment_guides(self):
        return []

    def individual_vertices(self):
        return []

    def individual_edges(self):
        return []


def marginal_increase(dist):
    if isinstance(dist, tuple):
        return dist[:-1] + (dist[-1] * 1.01,)
    else:
        return dist * 1.01

def find_closest(app, position, ignore=()):
    for attempt in [find_closest_vertex, find_closest_edge, find_closest_face]:
        if attempt in ignore:
            continue
        result = attempt(app, position, ignore=ignore)
        if result is not None:
            return result
    return SelectVoid(app, position)
    
def find_closest_vertex(app, position, ignore=()):
    closest = None
    distance_min = app.scale_ctrl(DISTANCE_VERTEX_MIN)
    for v in app.model.all_vertices():
        if v in ignore:
            continue
        distance = abs(position - v)
        if distance < distance_min:
            distance_min = distance * 1.01
            closest = SelectVertex(app, v)
    return closest

def find_closest_edge(app, position, ignore=()):
    closest = None
    distance_min = app.scale_ctrl(DISTANCE_EDGE_MIN)
    for e in app.model.edges:
        if e in ignore:
            continue
        frac, distance = e.measure_distance(position)
        if 0 < frac < 1 and distance < distance_min:
            distance_min = distance * 1.01
            if abs(position - (e.v1 + e.v2) * 0.5) < app.scale_ctrl(DISTANCE_VERTEX_MIN):
                frac = 0.5
            closest = SelectAlongEdge(app, e, frac)
    return closest

def find_closest_face(app, position, ignore=()):
    closest = None
    distance_min = app.scale_ctrl(DISTANCE_FACE_MIN)
    for face in app.model.faces:
        if face in ignore:
            continue
        signed_distance = face.plane.signed_distance_to_point(position)
        distance = abs(signed_distance)
        if distance < distance_min and face.point_is_inside(position):
            distance_min = distance * 1.01
            closest = SelectOnFace(app, face, position - face.plane.normal * signed_distance)
    return closest
