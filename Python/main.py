from app import App
from util import Vector3
from worldobj import *


def init(**kwds):
    app = App(**kwds)
    app.display(Polygon([Vector3(0, .5, 0), Vector3(0, 1, 0),
                         Vector3(1, 1, 0)]))
    app.display(ColoredPolygon([Vector3(0, 1, 0), Vector3(1, 1, 0),
                                Vector3(1, 1, 1), Vector3(0, 1, 1)],
                               color=0xFFC0C0))
    app.display(PolygonHighlight([Vector3(0, 1, 0), Vector3(1, 1, 0),
                                  Vector3(1, 1, 1), Vector3(0, 1, 1)],
                                 color=0x00FFFF))
    app.display(SmallSphere(Vector3(1, 1, 1), color=0xFF0000))
    app.display(Cylinder(Vector3(1, 1, 1), Vector3(0, 0.5, 0), color=0xD00000))
    return app
