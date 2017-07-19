from util import EPSILON


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


class RectanglePointer(WorldObject):
    _kind = 201

    def __init__(self, position):
        self.position = position

    def getrawdata(self):
        return self.position.tolist()

class CrossPointer(RectanglePointer):
    _kind = 202

class MovePointer(RectanglePointer):
    _kind = 203

class EraserPointer(RectanglePointer):
    _kind = 204

class PencilPointer(RectanglePointer):
    _kind = 205

class SelectPointer(RectanglePointer):
    _kind = 206

class SelectPointerPlus(RectanglePointer):
    _kind = 207

class SelectPointerMinus(RectanglePointer):
    _kind = 208

class PushPullPointer(RectanglePointer):
    _kind = 209


class Stem(WorldObject):
    _kind = 251

    def __init__(self, end1, end2, color, color2=None):
        self.end1 = end1
        self.end2 = end2
        self.color = color
        self.color2 = color2

    def getrawdata(self):
        lst = self.end1.tolist() + self.end2.tolist()
        lst.append(self.color)
        if self.color2 is not None:
            lst.append(self.color2)
        return lst


class Cylinder(Stem):
    _kind = 250


class DashedStem(Stem):
    _kind = 252


class SelectedStem(Stem):
    _kind = 253

    def __init__(self, end1, end2):
        Stem.__init__(self, end1, end2, 0)   # color is unused


def _text2raw(text):
    # 'text' can be a string or a unicode
    return [len(text)] + [ord(ch) for ch in text]

def distance2text(distance):
    if distance > 1.0 - EPSILON:
        return '%.2f m' % (distance,)
    else:
        return '%.0f cm' % (distance * 100.0,)

class TextHint(WorldObject):
    _kind = 150

    def __init__(self, end1, end2, text, ignore_controller_num=-1, manual_enter_token=-1):
        self.end1 = end1
        self.end2 = end2
        self.text = text
        self.ignore_controller_num = ignore_controller_num
        self.manual_enter_token = manual_enter_token

    def getrawdata(self):
        lst = _text2raw(self.text)
        lst.extend(self.end1.tolist())
        lst.extend(self.end2.tolist())
        lst.append(self.ignore_controller_num)
        lst.append(self.manual_enter_token)
        return lst