from worldobj import Cylinder, SmallSphere


DISTANCE_VERTEX_MIN = 0.05
DISTANCE_EDGE_MIN = 0.044
DISTANCE_FACE_MIN = 0.04

class HoverColorScheme:
    VERTEX = 0x80FFFF
    EDGE   = 0x00D0D0
    VOID   = 0x00A0A0

class SelectedColorScheme:
    VERTEX = 0xFF4040
    EDGE   = 0xD00000
    VOID   = 0xA00000

class TargetColorScheme:
    VERTEX = 0x80FF80
    EDGE   = 0x00D000
    VOID   = 0x00A000


class SelectVertex(object):
    def __init__(self, app, vertex):
        self.app = app
        self.vertex = vertex

    def flash(self, color_scheme):
        self.app.flash(SmallSphere(self.vertex.position, color_scheme.VERTEX))

    def get_point(self):
        return self.vertex.position


class SelectAlongEdge(object):
    def __init__(self, app, edge, fraction):
        self.app = app
        self.edge = edge
        self.fraction = fraction    # maybe rounded to exactly 0.5, for the middle

    def flash(self, color_scheme):
        p1 = self.edge.v1.position
        p2 = self.edge.v2.position
        self.app.flash(Cylinder(p1, p2, color_scheme.EDGE))
        color = color_scheme.EDGE if self.fraction != 0.5 else color_scheme.VERTEX
        self.app.flash(SmallSphere(p1 + (p2 - p1) * self.fraction, color))

    def get_point(self):
        p1 = self.edge.v1.position
        p2 = self.edge.v2.position
        return p1 + (p2 - p1) * self.fraction


class SelectVoid(object):
    def __init__(self, app, position):
        self.app = app
        self.position = position

    def flash(self, color_scheme):
        self.app.flash(SmallSphere(self.position, color_scheme.VOID))

    def get_point(self):
        return self.position


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
    return None  #xxx
