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

    v1 = Vector3(0, 0, 1)
    v2 = Vector3(1, 0, 1)
    v3 = Vector3(1, 1, 1)
    v4 = Vector3(0, 1, 1)
    step = ModelStep(app.model, "Initial rectangle")
    e1 = step.add_edge(v1, v2)
    e2 = step.add_edge(v2, v3)
    e3 = step.add_edge(v3, v4)
    e4 = step.add_edge(v4, v1)
    step.add_face([e1, e2, e3, e4])
    app.execute_step(step)

    return app
