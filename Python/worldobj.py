
class WorldObject(object):
    _index = None


class Polygon(WorldObject):
    _kind = 101

    def __init__(self, vertices):
        self.vertices = vertices
    
    def getrawdata(self):
        lst = []
        for v in self.vertices:
            lst += v.tolist()
        return lst


class ColoredPolygon(Polygon):
    _kind = 102

    def __init__(self, vertices, color):
        Polygon.__init__(self, vertices)
        self.color = color
    
    def getrawdata(self):
        lst = Polygon.getrawdata(self)
        lst.append(self.color)
        return lst


class PolygonHighlight(ColoredPolygon):
    _kind = 103


class SmallSphere(WorldObject):
    _kind = 200

    def __init__(self, center, color):
        self.center = center
        self.color = color

    def getrawdata(self):
        lst = self.center.tolist()
        lst.append(self.color)
        return lst


class Stem(WorldObject):
    _kind = 251

    def __init__(self, end1, end2, color):
        self.end1 = end1
        self.end2 = end2
        self.color = color

    def getrawdata(self):
        lst = self.end1.tolist() + self.end2.tolist()
        lst.append(self.color)
        return lst


class Cylinder(Stem):
    _kind = 250
