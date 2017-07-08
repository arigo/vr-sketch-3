import py
import math
from util import *


def test_vector():
    assert Vector3(1, 2, 3) == Vector3(1, 2, 3)
    assert Vector3(1, 2, 3.00000001) == Vector3(1, 2, 3)
    assert Vector3(1, 2, 3.001) != Vector3(1, 2, 3)
    assert (Vector3(1, 2, 3.001) == Vector3(1, 2, 3)) is False

    assert Vector3.from_axis('x') == Vector3(1, 0, 0)
    assert Vector3.from_axis('x', norm=3.45) == Vector3(3.45, 0, 0)

    assert Vector3(.1, .2, .3) + Vector3(.4, .5, .6) == Vector3(.5, .7, .9)
    assert Vector3(.9, .8, .7) - Vector3(.4, .5, .6) == Vector3(.5, .3, .1)
    assert Vector3(.1, .2, .3) * 4.5 == Vector3(.45, .9, 1.35)
    assert (-4.5) * Vector3(.1, .2, .3) == Vector3(-.45, -.9, -1.35)
    assert Vector3(1, 2, 3) / 5 == Vector3(.2, .4, .6)
    assert abs(Vector3(3, 4, 0)) == 5
    assert abs(Vector3(3, -4, 1)) == math.sqrt(26)
    assert Vector3(.5, 2, 3.5).dot(Vector3(4, 5, 6)) == 2 + 10 + 21
    assert Vector3(3, 4, 0).normalized() == Vector3(.6, .8, 0)
    assert Vector3(4, 5, 6).withcoord('y', 7) == Vector3(4, 7, 6)
    
    assert Vector3(5, 6, 2).closest_axis_plane(1.5) is None
    assert Vector3(5, 6, 1).closest_axis_plane(1.5) == 'z'
    assert Vector3(-1, 6, 1.2).closest_axis_plane(1.5) == 'x'
    assert Vector3(0.5, 0.4, -0.6).closest_axis_plane(1.5) == 'y'

    assert Vector3(4, 5, 6).project_orthogonal(Vector3(0, -2, 0)) == (
               Vector3(4, 0, 6))


def test_project_point_inside():
    pt = Vector3(4, 5, 6)
    assert WholeSpace().distance_to_point(pt) == 0.0
    assert WholeSpace().project_point_inside(pt) == pt

    assert Plane(Vector3(0, 1, 0), -4.75).distance_to_point(pt) == 0.25
    assert Plane(Vector3(0, 1, 0), -5.5).distance_to_point(pt) == 0.5
    assert Plane(Vector3(0, 1, 0), -4.75).project_point_inside(pt) == (
                     Vector3(4, 4.75, 6))
    assert Plane(Vector3(0, 1, 0), -5.5).project_point_inside(pt) == (
                     Vector3(4, 5.5, 6))

    line = Line(Vector3(2, 3.1, 4.2), Vector3(1, 0, 0))
    assert line.project_point_inside(pt) == Vector3(4, 3.1, 4.2)
    assert line.distance_to_point(pt) == abs(Vector3(0, 5 - 3.1, 6 - 4.2))

    pt2 = Vector3(6.21, .94, -5.1)
    assert SinglePoint(pt2).project_point_inside(pt) == pt2
    assert SinglePoint(pt2).distance_to_point(pt) == abs(pt2 - pt)


def test_intersect():
    assert WholeSpace().intersect("anything") == "anything"

    plane = Plane(Vector3(0, 1, 0), -5)
    line = Line(Vector3(2, 3.1, 4.2), Vector3(1, 0, 0))
    sp = SinglePoint(Vector3(4, 5, 6))

    assert plane.intersect(WholeSpace()) is plane
    assert plane.intersect(plane) is plane
    assert plane.intersect(Plane(Vector3(0, -1, 0), 5)) is plane
    py.test.raises(EmptyIntersection, plane.intersect,
                           Plane(Vector3(0, -1, 0), 5.1))
    inter = plane.intersect(Plane(Vector3(0, 0, 1), -7))
    assert isinstance(inter, Line)
    assert inter.distance_to_point(Vector3(12.34, 5, 7)) == 0
    d = inter.distance_to_point(Vector3(-12.34, 5-40, 7+30))
    assert abs(d - 50.0) < 0.001
    py.test.raises(EmptyIntersection, plane.intersect, line)
    inter = plane.intersect(Line(Vector3(2, 3.1, 4.2), Vector3(0, -1, 0)))
    assert isinstance(inter, SinglePoint)
    assert inter.position == Vector3(2, 5, 4.2)
    assert plane.intersect(sp) is sp
    py.test.raises(EmptyIntersection, plane.intersect,
                        SinglePoint(Vector3(4, 5.1, 6)))

    py.test.raises(EmptyIntersection, line.intersect, sp)
    assert Line(Vector3(4, 5, 0), Vector3(0, 0, -1)).intersect(sp) is sp
    assert line.intersect(WholeSpace()) is line
    py.test.raises(EmptyIntersection, line.intersect, plane)
    assert line.intersect(line) is line
    inter = line.intersect(Line(Vector3(6, 3.1, 8), Vector3(0, 0, -1)))
    assert isinstance(inter, SinglePoint)
    assert inter.position == Vector3(6, 3.1, 4.2)
    py.test.raises(EmptyIntersection, line.intersect,
                           Line(Vector3(6, 3.2, 8), Vector3(0, 0, -1)))
    inter = line.intersect(Plane(Vector3(-1, 0, 0), 6.78))
    assert isinstance(inter, SinglePoint)
    assert inter.position == Vector3(6.78, 3.1, 4.2)
    assert line.intersect(Plane(Vector3(0, -1, 0), 3.1)) is line
    py.test.raises(EmptyIntersection, line.intersect,
                          Plane(Vector3(0, -1, 0), 3.2))

    assert sp.intersect(sp) is sp
    assert sp.intersect(WholeSpace()) is sp
    assert sp.intersect(Line(Vector3(4, 5, 0), Vector3(0, 0, -1))) is sp
    py.test.raises(EmptyIntersection, sp.intersect,
                        Line(Vector3(4, 5.1, 0), Vector3(0, 0, -1)))

def test_shifted():
    delta = Vector3(4, 5, 6)
    sp = WholeSpace()
    assert sp.shifted(delta) is sp
    pl = Plane(Vector3(0, 1, 0), -4.75).shifted(delta)
    assert pl.normal == Vector3(0, 1, 0)
    assert pl.distance == -9.75
    ln = Line(Vector3(2, 3.1, 4.2), Vector3(1, 0, 0)).shifted(delta)
    assert ln.from_point == Vector3(6, 8.1, 10.2)
    assert ln.axis == Vector3(1, 0, 0)
    sp = SinglePoint(Vector3(1.1, 2.2, 3.3)).shifted(delta)
    assert sp.position == Vector3(5.1, 7.2, 9.3)

def test_v3dict():
    d = GeometryDict()
    k1 = Vector3(4, 5, 6)
    k2 = Vector3(4, 5, 6.1)
    d[k1] = 123
    d[k2] = 234
    assert d[k1] == 123
    assert d[k2] == 234
    assert k1 in d
    assert k2 in d
    assert Vector3(4, 5.00000001, 6) in d
    assert Vector3(4, 5.01, 6) not in d
    assert Vector3(4, 5 + EPSILON * 1.1, 6) not in d
    assert d[Vector3(4, 5.00000001, 6)] == 123
    d[Vector3(4, 5.00000001, 6)] = "foo"
    assert d[k1] == "foo"
    dkeys = d.keys()
    assert dkeys == [k1, k2] or dkeys == [k2, k1]

def test_planedict():
    d = GeometryDict()
    p1 = Plane(Vector3(4, 5, 6), 10)
    p2 = Plane(Vector3(4, 5, 6), 10.01)
    p3 = Plane(Vector3(4, 5.01, 6), 10.01)
    d[p1] = 123
    d[p2] = 234
    d[p3] = 345
    assert d[p1] == 123
    assert d.get(p2) == 234
    assert d.get(p3) == 345
    assert d.get(Plane(Vector3(4, 5, 6.01), 10)) is None
    assert Plane(Vector3(4, 5, 6.01), 10) not in d
    assert sorted(d.keys()) == sorted([p1, p2, p3])
