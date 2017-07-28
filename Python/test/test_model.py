import py
import math
from util import *
from model import *


def fake_approx_plane(lst):
    assert len(lst) >= 3
    for z in lst[2 : len(lst) : 3]:
        assert z == 1.0, "missing approx_plane: %r" % (lst,)
    return (0., 0., 1., -1.)

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
    gr = model.root_group
    e1 = step.add_edge(gr, v1, v2)
    e2 = step.add_edge(gr, v2, v3)
    e3 = step.add_edge(gr, v3, v4)
    e4 = step.add_edge(gr, v4, v1)
    step.add_face([e1, e2, e3, e4])
    step.check_valid()
    step._apply_to_model()
    
    assert len(model.get_faces(gr)) == 1
    assert len(model.get_edges(gr)) == 4
    assert model.get_faces(gr)[0].edges == [e1, e2, e3, e4]
    assert model.get_edges(gr) == [e1, e2, e3, e4]
    return model


def test_intersect_edge():
    gr = Group(None)
    e1 = Edge(gr, Vector3(0, 0, 3), Vector3(1, 0, 3))
    e2 = Edge(gr, Vector3(0.5, 0, 3), Vector3(0.5, 1, 3))
    e3 = Edge(gr, Vector3(0.5, 0.1, 3), Vector3(0.5, 1, 3))
    assert e1.intersect_edge(e2) == Vector3(0.5, 0, 3)
    assert e2.intersect_edge(e1) == Vector3(0.5, 0, 3)
    assert e1.intersect_edge(e3) is None
    assert e3.intersect_edge(e1) is None
    assert e2.intersect_edge(e3) is None
    assert e3.intersect_edge(e2) is None


def test_point_is_inside():
    v1 = Vector3(0, 0, 1)
    v2 = Vector3(1, 0, 1)
    v3 = Vector3(1, 1, 1)
    v4 = Vector3(0, 1, 1)
    v5 = Vector3(0.5, 0.5, 1)
    gr = Group(None)
    f = Face([Edge(gr, v2, v3),
              Edge(gr, v3, v4),
              Edge(gr, v4, v1),
              Edge(gr, v1, v5),
              Edge(gr, v5, v2)])
    assert not f.point_is_inside(Vector3(0.5, 0, 1))


def test_consolidate_subdivide_edges():
    model = test_initial_rectangle()
    v1 = Vector3(0.5, 0, 1)
    v2 = Vector3(0.5, 1, 1)
    step = ModelStep(model, "Split in two")
    gr = model.root_group
    step.add_edge(gr, v1, v2)
    while step.consolidate_subdivide_edges():
        pass
    
    assert len(step.fe_remove) == 3
    assert [fe for fe in step.fe_remove if isinstance(fe, Face)] == [model.get_faces(gr)[0]]
    medges = model.get_edges(gr)
    assert medges[0] in step.fe_remove
    assert medges[1] not in step.fe_remove
    assert medges[2] in step.fe_remove
    assert medges[3] not in step.fe_remove

    assert len(step.fe_add) == 6
    assert step.fe_add[0].v1 == Vector3(0.5, 0, 1)    #  +-----+
    assert step.fe_add[0].v2 == Vector3(0.5, 1, 1)    #  |  X  |
                                                      #  |  X  |
                                                      #  +-----+

    assert step.fe_add[1].edges == [step.fe_add[2], step.fe_add[3], medges[1], step.fe_add[4], step.fe_add[5], medges[3]]

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
    step.check_valid()

def test_consolidate_subdivide_face():
    model = test_initial_rectangle()
    v1 = Vector3(0, 0, 1)
    v2 = Vector3(1, 1, 1)
    step = ModelStep(model, "Split in two along the diagonal")
    gr = model.root_group
    step.add_edge(gr, v1, v2)
    while step.consolidate_subdivide_faces():
        pass
    
    assert len(step.fe_remove) == 1
    assert len([fe for fe in step.fe_add if isinstance(fe, Face)]) == 2
    assert len([fe for fe in step.fe_add if isinstance(fe, Edge)]) == 2

def test_consolidate_subdivide_face_2():
    model = test_initial_rectangle()
    v1 = Vector3(0, 0, 1)
    v2 = Vector3(.5, .5, 1)
    v3 = Vector3(1, 0, 1)
    step = ModelStep(model, "Split by adding a triangle along one edge")
    gr = model.root_group
    step.add_edge(gr, v1, v2)
    step.add_edge(gr, v2, v3)
    r = step.consolidate_subdivide_faces()
    assert r is True
    
    assert len(step.fe_remove) == 1
    assert len([fe for fe in step.fe_add if isinstance(fe, Face)]) == 2
    assert len([fe for fe in step.fe_add if isinstance(fe, Edge)]) == 4

    r = step.consolidate_subdivide_faces()
    assert r is False
    step.check_valid()

def test_consolidate_subdivide_edges_and_faces():
    model = test_initial_rectangle()
    v1 = Vector3(0.5, 0, 1)
    v2 = Vector3(0.5, 1, 1)
    step = ModelStep(model, "Split in two, and subdivide the face in addition to the edges")
    gr = model.root_group
    step.add_edge(gr, v1, v2)
    while step.consolidate_subdivide_edges():
        pass
    step.check_valid()
    r = step.consolidate_subdivide_faces()
    assert r is True
    step.check_valid()
    r = step.consolidate_subdivide_faces()
    assert r is False
    step.check_valid()
    assert len([fe for fe in step.fe_remove if isinstance(fe, Face)]) == 1
    assert len([fe for fe in step.fe_remove if isinstance(fe, Edge)]) == 2
    assert len([fe for fe in step.fe_add if isinstance(fe, Face)]) == 2
    assert len([fe for fe in step.fe_add if isinstance(fe, Edge)]) == 6
