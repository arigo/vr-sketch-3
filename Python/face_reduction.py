from util import EPSILON, Plane, GeometryDict
import model


def all_potential_planes(model, group):
    if "potential_planes" not in group.caches:
        result = GeometryDict()
        medges = model.get_edges(group)
        for edge1 in medges:
            for edge2 in medges:
                if edge1.v2 == edge2.v1 or edge1.v2 == edge2.v2:
                    normal = (edge1.v2 - edge1.v1).cross(edge2.v2 - edge2.v1)
                    normal_length = abs(normal)
                    if normal_length > EPSILON:
                        normal /= normal_length
                        result[Plane.from_point_and_normal(edge1.v2, normal)] = True
        group.caches["potential_planes"] = result.keys()
    return group.caches["potential_planes"]

def potential_new_face(model, group, point, max_distance=EPSILON):
    best_vertices = None
    best_distance = max_distance
    for plane in all_potential_planes(model, group):
        # if the plane is farther than the previous best, ignore
        distance = plane.distance_to_point(point)
        if distance > best_distance:
            continue
        # if the point is already inside a face, reject that plane
        #for face in model.get_faces(group):
        #    if face.plane.distance_to_point(point) <= max_distance and face.point_is_inside(point):
        #        break
        #else:
        new_vertices = can_add_new_face_in_plane(model, group, point, plane)
        if new_vertices is not None:
            best_distance = distance * 1.01
            best_vertices = new_vertices
    return best_vertices

def can_add_new_face_in_plane(model, group, point, plane):
    # build a list of edges in that plane, and sort it by distance to the point
    planar_edges = []
    for edge in model.get_edges(group):
        if (plane.distance_to_point(edge.v1) < EPSILON and
            plane.distance_to_point(edge.v2) < EPSILON):
            planar_edges.append(edge)
    planar_edges.sort(key=lambda edge: edge.distance_to_point(point))

    # try to build a closed path of edges that completely goes around the point,
    # by starting from the closest of the edges and extending it such that it
    # keep going in the same direction around the point.  XXX This is an
    # imperfect heuristic.
    def getdir(edge):
        return (edge.v2 - edge.v1).cross(point - edge.v1).dot(plane.normal) < 0.0

    if not planar_edges:
        return None
    edge = planar_edges.pop(0)
    direction = getdir(edge)
    source_point = edge.v1
    new_vertices = [edge.v2]

    while new_vertices[-1] != source_point:
        v_from = new_vertices[-1]
        for edge1 in planar_edges:   # in sorted order, so prefer the edges that come closer
            vs = (edge1.v1, edge1.v2) if getdir(edge1) == direction else (edge1.v2, edge1.v1)
            if vs[0] == v_from:
                v_to = vs[1]
                break
        else:
            return None
        planar_edges.remove(edge1)
        new_vertices.append(v_to)

    return new_vertices
