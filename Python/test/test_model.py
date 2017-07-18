import py
import math
from util import *
from model import *


RECORD = {}
RECORD[0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1] = (0.0, 0.0, 1.0, 1.0)

def fake_approx_plane(lst):
    try:
        return RECORD[tuple(lst)]
    except KeyError:
        raise AssertionError("missing RECORD for approx_plane: %r" % (lst,))

def setup_module(mod):
    import util
    util._approx_plane = fake_approx_plane


def test_initial_rectangle():
    model = Model()
    v1 = Vector3(0, 0, 1)
    v2 = Vector3(1, 0, 1)
    v3 = Vector3(1, 1, 1)
    v4 = Vector3(0, 1, 1)
    step = ModelStep(model, "Initial rectangle")
    e1 = step.add_edge(v1, v2)
    e2 = step.add_edge(v2, v3)
    e3 = step.add_edge(v3, v4)
    e4 = step.add_edge(v4, v1)
    step.add_face([e1, e2, e3, e4])
    step._apply_to_model()
    
    assert len(model.faces) == 1
    assert len(model.edges) == 4
    assert model.faces[0].edges == [e1, e2, e3, e4]
    assert model.edges == [e1, e2, e3, e4]
    return model


def test_intersect_edge():
    e1 = Edge(Vector3(0, 0, 3), Vector3(1, 0, 3))
    e2 = Edge(Vector3(0.5, 0, 3), Vector3(0.5, 1, 3))
    e3 = Edge(Vector3(0.5, 0.1, 3), Vector3(0.5, 1, 3))
    assert e1.intersect_edge(e2) == Vector3(0.5, 0, 3)
    assert e2.intersect_edge(e1) == Vector3(0.5, 0, 3)
    assert e1.intersect_edge(e3) is None
    assert e3.intersect_edge(e1) is None
    assert e2.intersect_edge(e3) is None
    assert e3.intersect_edge(e2) is None


def test_consolidate_subdivide_edges():
    model = test_initial_rectangle()
    v1 = Vector3(0.5, 0, 1)
    v2 = Vector3(0.5, 1, 1)
    step = ModelStep(model, "Split in two")
    step.add_edge(v1, v2)
    while step.consolidate_subdivide_edges():
        pass
    
    assert len(step.fe_remove) == 3
    assert [fe for fe in step.fe_remove if isinstance(fe, Face)] == [model.faces[0]]
    assert model.edges[0] in step.fe_remove
    assert model.edges[1] not in step.fe_remove
    assert model.edges[2] in step.fe_remove
    assert model.edges[3] not in step.fe_remove

    assert len(step.fe_add) == 6
    assert step.fe_add[0].v1 == Vector3(0.5, 0, 1)    #  +-----+
    assert step.fe_add[0].v2 == Vector3(0.5, 1, 1)    #  |  X  |
                                                      #  |  X  |
                                                      #  +-----+

    assert step.fe_add[1].edges == [step.fe_add[2], step.fe_add[3], model.edges[1], step.fe_add[4], step.fe_add[5], model.edges[3]]

    assert step.fe_add[2].v1 == Vector3(0,   0, 1)    #  +XX---+
    assert step.fe_add[2].v2 == Vector3(0.5, 0, 1)    #  |  |  |
                                                      #  |  |  |
                                                      #  +-----+

    assert step.fe_add[3].v1 == Vector3(0.5, 0, 1)    #  +---XX+
    assert step.fe_add[3].v2 == Vector3(1  , 0, 1)    #  |  |  |
                                                      #  |  |  |
                                                      #  +-----+

    assert step.fe_add[4].v1 == Vector3(1  , 1, 1)    #  +-----+
    assert step.fe_add[4].v2 == Vector3(0.5, 1, 1)    #  |  |  |
                                                      #  |  |  |
                                                      #  +---XX+

    assert step.fe_add[5].v1 == Vector3(0.5, 1, 1)    #  +-----+
    assert step.fe_add[5].v2 == Vector3(0  , 1, 1)    #  |  |  |
                                                      #  |  |  |
                                                      #  +XX---+
