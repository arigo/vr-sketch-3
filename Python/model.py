from util import Vector3
import worldobj


INF = float("inf")


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
        self._check_invariant()

    def _check_invariant(self):
        edges = self.edges
        for i in range(len(edges)):
            assert edges[i-1].v2 is edges[i].v1

    def getrawdata(self):
        self._check_invariant()
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
