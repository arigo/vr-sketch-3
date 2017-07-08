from util import Vector3, Plane, EPSILON
import worldobj


class Edge(object):
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2

    def measure_distance(self, position):
        # returns (fraction along the edge, distance from the line supporting the edge)
        v1 = self.v1
        v2 = self.v2
        p1 = v2 - v1
        p2 = position - v1
        dot = p1.dot(p2)
        length2 = p1.dot(p1)
        frac = dot / length2 if length2 else 0.0
        return frac, abs(p2 - p1 * frac)

    def distance_to_point(self, point):
        # returns the 3D distance from the point to the edge
        frac, distance_to_line = self.measure_distance(point)
        if frac <= 0:
            return abs(self.v1 - point)
        elif frac >= 1:
            return abs(self.v2 - point)
        else:
            return distance_to_line


class Face(object):
    def __init__(self, edges):
        self.edges = edges
        self._update_plane()

    def _update_plane(self):
        # check invariants
        edges = self.edges
        for i in range(len(edges)):
            assert edges[i-1].v2 == edges[i].v1
        # compute the plane that is the best approximation of all vertices
        self.plane = Plane.from_vertices([edge.v1 for edge in self.edges])

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
        uvs = [self._project_point_on_plane(edge.v1) for edge in self.edges]
        uv2 = uvs[0]
        side = 0
        for i in range(len(uvs) - 1, -1, -1):
            uv1 = uvs[i]
            if (uv1[1] < pt[1]) != (uv2[1] < pt[1]):
                # (x - uv1[0]) / (uv2[0] - uv1[0]) == (pt[1] - uv1[1]) / (uv2[1] - uv1[1])
                x = uv1[0] + (uv2[0] - uv1[0]) * (pt[1] - uv1[1]) / (uv2[1] - uv1[1])
                if x < pt[0]:
                    side += -1 if uv1[1] < uv2[1] else 1
            uv2 = uv1
        return side != 0


class Model(object):

    def __init__(self):
        self.edges = []
        self.faces = []
        self.caches = {}

    def all_vertices(self):
        for edge in self.edges:
            yield edge.v1
            yield edge.v2


class ModelStep(object):

    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.fe_remove = set()
        self.fe_add = []

    def apply(self, app):
        for edge_or_face in self.fe_remove:
            app._remove_edge_or_face(edge_or_face)
        for edge_or_face in self.fe_add:
            app._add_edge_or_face(edge_or_face)

        fe_remove = self.fe_remove
        self.model.edges = [edge for edge in self.model.edges if edge not in fe_remove]
        self.model.faces = [face for face in self.model.faces if face not in fe_remove]
        for edge_or_face in self.fe_add:
            if isinstance(edge_or_face, Edge):
                self.model.edges.append(edge_or_face)
            elif isinstance(edge_or_face, Face):
                self.model.faces.append(edge_or_face)
            else:
                raise AssertionError

    def reversed(self):
        ms = ModelStep(self.model, self.name)
        ms.fe_remove.update(self.fe_add)
        ms.fe_add.extend(self.fe_remove)
        return ms

    def add_edge(self, v1, v2):
        for edge in self.model.edges:
            if edge.v1 == v1 and edge.v2 == v2 and edge not in self.fe_remove:
                return edge
        for edge in self.fe_add:
            if isinstance(edge, Edge) and edge.v1 == v1 and edge.v2 == v2:
                return edge
        edge = Edge(v1, v2)
        self.fe_add.append(edge)
        return edge

    def add_face(self, edges):
        face = Face(edges)
        self.fe_add.append(face)
        return face

    def remove(self, edge_or_face):
        self.fe_remove.add(edge_or_face)

    def move_vertices(self, old2new, move_edges, move_faces):
        self.fe_remove.update(move_edges)
        self.fe_remove.update(move_faces)
        edges_old2new = {}

        def map_v(v):
            for v_old, v_new in old2new:
                if v_old == v:
                    return v_new
            return v
        # xxx bad complexity here
        for edge in move_edges:
            edges_old2new[edge] = self.add_edge(map_v(edge.v1), map_v(edge.v2))
        for face in move_faces:
            edges = [edges_old2new.get(edge, edge) for edge in face.edges]
            self.add_face(edges)

    def _adjust(self, v_old, v_new):
        for fe in self.fe_add:
            if isinstance(fe, Edge):
                if fe.v1 == v_old: fe.v1 = v_new
                if fe.v2 == v_old: fe.v2 = v_new

    def _adjust_vertex_to_old_position(self, v):
        for edge in self.model.edges:
            if edge.v1 == v: return edge.v1
            if edge.v2 == v: return edge.v2
        return v

    def consolidate(self, app):
        # - remove zero-lengh edges, and zero-edges faces
        for fe in self.fe_add[:]:
            if isinstance(fe, Edge) and fe.v1 == fe.v2:
                self.fe_add.remove(fe)
                v = (fe.v1 + fe.v2) * 0.5     # they may not be *exactly* equal
                v = self._adjust_vertex_to_old_position(v)
                self._adjust(fe.v1, v)
                self._adjust(fe.v2, v)
        for fe in self.fe_add[:]:
            if isinstance(fe, Face):
                fe.edges = [edge for edge in fe.edges if not edge.v1.exactly_equal(edge.v2)]
                if len(fe.edges) == 0:
                    self.fe_add.remove(fe)

        # - subdivide faces if there are new edges in the middle of them
        # XXX NOT IMPLEMENTED YET

        # - remove duplicate faces
        # XXX NOT IMPLEMENTED YET

        # - assert that all the edges of the faces are present
        all_edges = set(self.model.edges) - self.fe_remove
        for fe in self.fe_add:
            if isinstance(fe, Edge):
                all_edges.add(fe)
        for fe in self.fe_add:
            if isinstance(fe, Face):
                for edge in fe.edges:
                    assert edge in all_edges

        # - remove the caches
        self.model.caches.clear()