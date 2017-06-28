from util import Vector3, Plane, EPSILON
import worldobj


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
        self.update_plane()

    def update_plane(self):
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

    def find_vertex(self, vertex):
        for i, edge in enumerate(self.edges):
            if edge.v1 is vertex:
                return i
        return -1

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

    def _new_or_existing_edge(self, v1, v2, create_list):
        for edge in self.edges:
            if edge.v1 is v1 and edge.v2 is v2:
                return edge
        edge = Edge(v1, v2)
        self.edges.append(edge)
        create_list.append(edge)
        return edge

    def _new_face(self, edges, create_list):
        face = Face(edges)
        self.faces.append(face)
        create_list.append(face)
        return face


class UndoRectangle(object):
    name = 'Rectangle'

    def __init__(self, positions):
        self.positions = positions

    def redo(self, app, model):
        v_list = [model.new_vertex(position) for position in self.positions]
        self.create_list = []
        e_list = []
        for i in range(len(v_list)):
            e_list.append(model._new_or_existing_edge(v_list[i - 1], v_list[i], self.create_list))
        model._new_face(e_list, self.create_list)
        for x in self.create_list:
            app.display(x)

    def undo(self, app, model):
        for x in self.create_list:
            if isinstance(x, Edge):
                model.edges.remove(x)
            else:
                model.faces.remove(x)
            app.destroy(x)
        del self.create_list


class UndoMove(object):
    
    def __init__(self, vertices):
        self.v2positions = {}
        for v in vertices:
            self.v2positions[v] = v.position
        if len(self.v2positions) == 1:
            self.name = 'Move vertex'
        else:
            self.name = 'Move %d vertices' % (len(self.v2positions),)

    def undo(self, app, model):
        self.v2positions_after = {}
        for vertex in self.v2positions.keys():
            self.v2positions_after[vertex] = vertex.position
        self.update_to(self.v2positions, app, model)

    def redo(self, app, model):
        self.update_to(self.v2positions_after, app, model)

    def update_to(self, new_v2positions, app, model):
        for vertex in new_v2positions.keys():
            vertex.position = new_v2positions[vertex]
        self.refresh(app, model)

    def refresh(self, app, model):
        for edge in model.edges:
            if edge.v1 in self.v2positions or edge.v2 in self.v2positions:
                app.display(edge)
        for face in model.faces:
            for e in face.edges:
                if e.v1 in self.v2positions:
                    face.update_plane()
                    app.display(face)
                    break
