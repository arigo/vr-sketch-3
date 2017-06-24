from util import Vector3, Plane
import worldobj


INF = float("inf")
EPSILON = 1e-4


class Vertex(object):
    
    def __init__(self, position):
        self.position = position


class Edge(worldobj.WorldObject):
    _kind = worldobj.Stem._kind

    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2

    def measure_distance(self, position):
        # returns (fraction along the edge, distance)
        v1 = self.v1.position
        v2 = self.v2.position
        p1 = v2 - v1
        p2 = position - v1
        dot = p1.dot(p2)
        length2 = p1.dot(p1)
        frac = dot / length2 if length2 else 0.0
        return frac, abs(p2 - p1 * frac)

    def getrawdata(self):
        lst = self.v1.position.tolist() + self.v2.position.tolist()
        lst.append(0x101010)   # very dark
        return lst


class Face(worldobj.WorldObject):
    _kind = worldobj.Polygon._kind

    def __init__(self, edges):
        self.edges = edges
        self.updated()

    def updated(self):
        # check invariants
        edges = self.edges
        for i in range(len(edges)):
            assert edges[i-1].v2 is edges[i].v1
        # compute the plane that is the best approximation of all vertices
        self.plane = Plane.from_vertices([edge.v1.position for edge in self.edges])

        normal = self.plane.normal
        if abs(normal.y) < max(abs(normal.x), abs(normal.z)):
            plane1 = Vector3(-normal.z, 0., normal.x)
        else:
            plane1 = Vector3(normal.y, -normal.x, 0.)
        self.planar_v1 = plane1.normalized()
        self.planar_v2 = normal.cross(self.planar_v1)

    def _project_point_on_plane(self, point):
        return (self.planar_v1.dot(point), self.planar_v2.dot(point))

    def point_is_inside(self, point):
        # NB. the face should be quasi-planar, but not necessarily convex
        pt = self._project_point_on_plane(point)
        uvs = [self._project_point_on_plane(edge.v1.position) for edge in self.edges]
        uv2 = uvs[0]
        side = 0
        for i in range(len(uvs) - 1, -1, -1):
            uv1 = uvs[i]
            if (uv1[1] < pt[1]) != (uv2[1] < pt[1]):
                x = (uv1[0] * uv2[1] - uv2[0] * uv1[1]) / (uv2[1] - uv1[1])
                if x < pt[0]:
                    side += -1 if uv1[1] < uv2[1] else 1
            uv2 = uv1
        return side != 0

    def getrawdata(self):
        lst = []
        for edge in self.edges:
            lst += edge.v1.position.tolist()
        return lst


class Model(object):

    def __init__(self):
        self.edges = []
        self.faces = []

    def all_vertices(self):
        for edge in self.edges:
            yield edge.v1
            yield edge.v2

    def new_vertex(self, position):
        for v in self.all_vertices():
            if abs(v.position - position) < EPSILON:
                return v
        return Vertex(position)

    def new_edge(self, app, v1, v2):
        for edge in self.edges:
            if edge.v1 is v1 and edge.v2 is v2:
                return edge
        e = Edge(v1, v2)
        app.add_edge(e)
        return e

    def new_face(self, app, edges):
        f = Face(edges)
        app.add_face(f)
        return f

    def new_face_from_vertices(self, app, vertices):
        v_list = [self.new_vertex(position) for position in vertices]
        e_list = [self.new_edge(app, v_list[i - 1], v_list[i]) for i in range(len(v_list))]
        return self.new_face(app, e_list)