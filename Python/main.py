from app import App, initialize_functions
from util import Vector3
from worldobj import *
from model import *


def init(ffi, *fns):
    initialize_functions(ffi, *fns)

    app = App()
    #app.display(Polygon([Vector3(0, .5, 0), Vector3(0, 1, 0),
    #                     Vector3(1, 1, 0)]))
    #app.display(ColoredPolygon([Vector3(0, 1, 0), Vector3(1, 1, 0),
    #                            Vector3(1, 1, 1), Vector3(0, 1, 1)],
    #                           color=0xFFC0C0))
    #app.display(PolygonHighlight([Vector3(0, 1, 0), Vector3(1, 1, 0),
    #                              Vector3(1, 1, 1), Vector3(0, 1, 1)],
    #                             color=0x00FFFF))
    #app.display(SmallSphere(Vector3(1, 1, 1), color=0xFF0000))
    #app.display(Cylinder(Vector3(1, 1, 1), Vector3(0, 0.5, 0), color=0xD00000))

    v1 = Vertex(Vector3(0, 0, 1))
    v2 = Vertex(Vector3(1, 0, 1))
    v3 = Vertex(Vector3(1, 1, 1))
    v4 = Vertex(Vector3(0, 1, 1))
    e1 = Edge(v1, v2); app.add_edge(e1)
    e2 = Edge(v2, v3); app.add_edge(e2)
    e3 = Edge(v3, v4); app.add_edge(e3)
    e4 = Edge(v4, v1); app.add_edge(e4)
    app.add_face(Face([e1, e2, e3, e4]))

    return app
