import math
from util import Vector3, Plane, Line, SinglePoint, EPSILON, EmptyIntersection, GeometryDict


class Edge(object):
    _NUMBER = 1

    def __init__(self, group, v1, v2, eid=None):
        assert isinstance(group, Group)
        self.group = group
        self.v1 = v1
        self.v2 = v2
        if eid is None:
            eid = Edge._NUMBER
        if Edge._NUMBER <= eid:
            Edge._NUMBER = eid + 1
        self.eid = eid

    def __repr__(self):
        return '<Edge %d: %r - %r>' % (self.eid, self.v1, self.v2)

    def measure_distance(self, position):
        # returns (fraction along the edge, distance from the line supporting the edge)
        v1 = self.v1
        v2 = self.v2
        p1 = v2 - v1
        p2 = position - v1
        dot = p1.dot(p2)
        length2 = p1.dot(p1)
        frac = dot / length2 if length2 else 0.0
        return frac, abs(p2 - p1 * frac)

    def distance_to_point(self, point):
        # returns the 3D distance from the point to the edge
        frac, distance_to_line = self.measure_distance(point)
        if frac <= 0:
            return abs(self.v1 - point)
        elif frac >= 1:
            return abs(self.v2 - point)
        else:
            return distance_to_line

    def supporting_line(self):
        # Returns the Line containing the edge, or the SinglePoint if the length is ~0
        middle = (self.v1 + self.v2) * 0.5
        v = self.v1 - self.v2
        length = abs(v)
        if length < EPSILON:
            return SinglePoint(middle)
        return Line(middle, v / length)

    def intersect_edge(self, other_edge):
        # Return None if the two edges are not coplanar, if they miss each other,
        # or if they are colinear.  Return the intersection point otherwise.
        line1 = self.supporting_line()
        line2 = other_edge.supporting_line()
        try:
            sp = line1.intersect(line2)
        except EmptyIntersection:
            return None
        if isinstance(sp, SinglePoint):
            point = sp.position
            if point.between(self.v1, self.v2) and point.between(other_edge.v1, other_edge.v2):
                return point
        return None

    def in_plane(self, plane):
        return plane.distance_to_point(self.v1) < EPSILON and plane.distance_to_point(self.v2) < EPSILON

    def point_is_inside(self, point):
        frac, distance = self.measure_distance(point)
        return -EPSILON < frac < 1 + EPSILON and distance < EPSILON


class Face(object):
    _NUMBER = 1
    _UPDATE_PLANE = True
    group = None

    def __init__(self, edges, fid=None):
        self.group = edges[0].group
        for edge in edges:
            assert edge.group is self.group
        self.edges = edges
        if fid is None:
            fid = Face._NUMBER
        if Face._NUMBER <= fid:
            Face._NUMBER = fid + 1
        self.fid = fid
        if Face._UPDATE_PLANE:
            self._update_plane()

    def __repr__(self):
        return '<Face %d: %r>' % (self.fid, ' - '.join([repr(e.v1) for e in self.edges]))

    def _update_plane(self):
        # check invariants
        edges = self.edges
        for i in range(len(edges)):
            assert edges[i-1].v2 == edges[i].v1
        # compute the plane that is the best approximation of all vertices
        self.plane = Plane.from_vertices([edge.v1 for edge in self.edges])

        normal = self.plane.normal
        if abs(normal.y) < max(abs(normal.x), abs(normal.z)):
            plane1 = Vector3(-normal.z, 0., normal.x)
        else:
            plane1 = Vector3(normal.y, -normal.x, 0.)
        self.planar_v1 = plane1.normalized()
        self.planar_v2 = normal.cross(self.planar_v1)

    def _project_point_on_plane(self, point):
        return (self.planar_v1.dot(point), self.planar_v2.dot(point))

    def point_is_inside(self, point):
        # NB. the face should be quasi-planar, but not necessarily convex
        pt = self._project_point_on_plane(point)
        uvs = [self._project_point_on_plane(edge.v1) for edge in self.edges]
        uv2 = uvs[0]
        side = 0
        for i in range(len(uvs) - 1, -1, -1):
            uv1 = uvs[i]
            if (uv1[1] < pt[1]) != (uv2[1] < pt[1]):
                # (x - uv1[0]) / (uv2[0] - uv1[0]) == (pt[1] - uv1[1]) / (uv2[1] - uv1[1])
                x = uv1[0] + (uv2[0] - uv1[0]) * (pt[1] - uv1[1]) / (uv2[1] - uv1[1])
                if x < pt[0]:
                    side += -1 if uv1[1] < uv2[1] else 1
            uv2 = uv1
        return side != 0


class Model(object):

    def __init__(self):
        self.root_group = Group(parent=None)
        self.group_edges = {}     # {Group: list-of-Edges}
        self.group_faces = {}     # {Group: list-of-Faces}

    def get_edges(self, group):
        if isinstance(group, set):
            result = []
            for gr1 in group:
                result += self.get_edges(gr1)
            return result
        assert isinstance(group, Group)
        return self.group_edges.setdefault(group, [])

    def get_edges_with_group(self, group):
        if group is None:
            group = set(self.group_edges)
        elif not isinstance(group, set):
            group = (group,)
        result = []
        for gr1 in group:
            for edge in self.get_edges(gr1):
                result.append((edge, gr1))
        return result

    def get_faces(self, group):
        if isinstance(group, set):
            result = []
            for gr1 in group:
                result += self.get_faces(gr1)
            return result
        assert isinstance(group, Group)
        return self.group_faces.setdefault(group, [])

    def get_groups(self):
        result = set(self.group_edges)
        result.update(self.group_faces)
        return result

    def all_vertices(self, only_group=None):
        result = []
        for edge in self.all_edges(only_group):
            result.append(edge.v1)
            result.append(edge.v2)
        return result

    def all_vertices_with_group(self, only_group):
        result = []
        for edge, group in self.get_edges_with_group(only_group):
            result.append((edge.v1, group))
            result.append((edge.v2, group))
        return result

    def all_edges(self, only_group=None):
        if only_group is not None:
            return list(self.get_edges(only_group))
        result = []
        for key, value in self.group_edges.items():
            result += value
        return result

    def all_faces(self, only_group=None):
        if only_group is not None:
            return list(self.get_faces(only_group))
        result = []
        for key, value in self.group_faces.items():
            result += value
        return result

    def get_bounding_box(self, group=None, extra=0.):
        try:
            vmin, vmax = group.caches['bounding_box']
        except KeyError:
            v_list = self.all_vertices(group)
            if not v_list:
                return Vector3(0., 0., 0.), Vector3(0., 0., 0.)
            vmin = Vector3(min(v.x for v in v_list),
                           min(v.y for v in v_list),
                           min(v.z for v in v_list))
            vmax = Vector3(max(v.x for v in v_list),
                           max(v.y for v in v_list),
                           max(v.z for v in v_list))
            group.caches['bounding_box'] = vmin, vmax
        return (Vector3(vmin.x - extra, vmin.y - extra, vmin.z - extra),
                Vector3(vmax.x + extra, vmax.y + extra, vmax.z + extra))

    def get_subgroups(self, group):
        try:
            return group.caches['subgroups']
        except KeyError:
            result = set()
            for gr1 in self.get_groups():
                if gr1.issubgroup(group):
                    result.add(gr1)
            group.caches['subgroups'] = result
            return result


class Group(object):
    _NUMBER = 1

    def __init__(self, parent, gid=None):
        self.parent = parent
        self.caches = {}
        if gid is None:
            gid = Group._NUMBER
        if Group._NUMBER <= gid:
            Group._NUMBER = gid + 1
        self.gid = gid

    def __repr__(self):
        return '<Group %d>' % (self.gid,)

    def issubgroup(self, parentgroup):
        while True:
            if self is parentgroup:
                return True
            self = self.parent
            if self is None:
                return False


class ModelStep(object):

    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.fe_remove = set()
        self.fe_add = []

    def apply(self, app):
        for edge_or_face in self.fe_remove:
            app._remove_edge_or_face(edge_or_face)
        for edge_or_face in self.fe_add:
            app._add_edge_or_face(edge_or_face)
        self._apply_to_model()
        #
        if app.selected_edges:
            old_sel = set()
            for edge in app.selected_edges:
                old_sel.add(edge.eid)
            app.selected_edges.clear()
            for edge in app.model.get_edges(app.curgroup):
                if edge.eid in old_sel:
                    app.selected_edges.add(edge)
            app.selection_updated()

    def _apply_to_model(self):
        # - first, remove the caches
        for group in self.model.get_groups():
            group.caches.clear()
        #
        fe_remove = self.fe_remove
        for group in self._all_removed_groups():
            edges = self.model.get_edges(group)
            edges[:] = [edge for edge in edges if edge not in fe_remove]
            faces = self.model.get_faces(group)
            faces[:] = [face for face in faces if face not in fe_remove]
        #
        for edge_or_face in self.fe_add:
            if isinstance(edge_or_face, Edge):
                self.model.get_edges(edge_or_face.group).append(edge_or_face)
            elif isinstance(edge_or_face, Face):
                self.model.get_faces(edge_or_face.group).append(edge_or_face)
            else:
                raise AssertionError

    def reversed(self):
        ms = ModelStep(self.model, self.name)
        ms.fe_remove.update(self.fe_add)
        ms.fe_add.extend(self.fe_remove)
        return ms

    def add_edge(self, group, v1, v2, paired_with=None):
        for edge in self.model.get_edges(group):
            if edge.v1 == v1 and edge.v2 == v2 and edge not in self.fe_remove:
                return edge
        for edge in self.fe_add:
            if isinstance(edge, Edge) and edge.v1 == v1 and edge.v2 == v2 and edge.group is group:
                return edge
        edge = Edge(group, v1, v2, None if paired_with is None else paired_with.eid)
        self.fe_add.append(edge)
        return edge

    def add_face(self, edges):
        face = Face(edges)
        self.fe_add.append(face)
        return face

    def remove(self, edge_or_face):
        self.fe_remove.add(edge_or_face)

    def _move_by(self, map_v, move_edges, move_faces):
        self.fe_remove.update(move_edges)
        self.fe_remove.update(move_faces)
        edges_old2new = {}

        # xxx bad complexity here
        for edge in move_edges:
            edges_old2new[edge] = self.add_edge(edge.group, map_v(edge.v1), map_v(edge.v2),
                                                paired_with=edge)
        for face in move_faces:
            edges = [edges_old2new.get(edge, edge) for edge in face.edges]
            self.add_face(edges)

    def move_vertices(self, old2new, move_edges, move_faces):
        def map_v(v):
            for v_old, v_new in old2new:
                if v_old == v:
                    return v_new
            return v
        self._move_by(map_v, move_edges, move_faces)

    def move_group_and_subgroups(self, start_group, delta):
        for group in self.model.get_subgroups(start_group):
            move_edges = self.model.get_edges(group)
            move_faces = self.model.get_faces(group)
            self._move_by(lambda v: v + delta, move_edges, move_faces)

    def _adjust(self, v_old, v_new):
        for fe in self.fe_add:
            if isinstance(fe, Edge):
                if fe.v1 == v_old: fe.v1 = v_new
                if fe.v2 == v_old: fe.v2 = v_new

    def _adjust_vertex_to_old_position(self, group, v):
        for edge in self.model.get_edges(group):
            if edge.v1 == v: return edge.v1
            if edge.v2 == v: return edge.v2
        return v

    def consolidate_temporary(self):
        # - remove zero-lengh edges, and zero-edges faces
        for fe in self.fe_add[:]:
            if isinstance(fe, Edge) and fe.v1 == fe.v2:
                self.fe_add.remove(fe)
                v = (fe.v1 + fe.v2) * 0.5     # they may not be *exactly* equal
                v = self._adjust_vertex_to_old_position(fe.group, v)
                self._adjust(fe.v1, v)
                self._adjust(fe.v2, v)
        for fe in self.fe_add[:]:
            if isinstance(fe, Face):
                fe.edges = [edge for edge in fe.edges if not edge.v1.exactly_equal(edge.v2)]
                if len(fe.edges) == 0:
                    self.fe_add.remove(fe)

    def _all_groups(self):
        all_groups = self.model.get_groups()
        for fe in self.fe_add:
            all_groups.add(fe.group)
        return all_groups

    def _all_changed_groups(self):
        all_groups = set()
        for fe in self.fe_remove:
            all_groups.add(fe.group)
        for fe in self.fe_add:
            all_groups.add(fe.group)
        return all_groups

    def _all_removed_groups(self):
        all_groups = set()
        for fe in self.fe_remove:
            all_groups.add(fe.group)
        return all_groups

    def _all_active_edges(self, group):
        all_edges = set(self.model.get_edges(group)) - self.fe_remove
        for fe in self.fe_add:
            if isinstance(fe, Edge) and fe.group is group:
                assert fe not in self.fe_remove
                all_edges.add(fe)
        return all_edges

    def _all_active_faces(self, group):
        all_faces = set(self.model.get_faces(group)) - self.fe_remove
        for fe in self.fe_add:
            if isinstance(fe, Face) and fe.group is group:
                assert fe not in self.fe_remove
                all_faces.add(fe)
        return all_faces

    def _remove_edge_and_add_copy(self, edge):
        assert isinstance(edge, Edge)
        assert edge not in self.fe_remove
        self.fe_remove.add(edge)
        copy = Edge(edge.group, edge.v1, edge.v2)
        self.fe_add.append(copy)
        #
        for face in self._all_active_faces(edge.group):
            if edge in face.edges:
                try:
                    self.fe_add.remove(face)
                except ValueError:
                    self.fe_remove.add(face)
                edges = face.edges[:]
                i = edges.index(edge)
                edges[i] = copy
                self.fe_add.append(Face(edges))
        return copy

    def consolidate_subdivide_edges_group(self, group):
        # find edges in the existing model that need to be split, and remove-readd them
        for fe in self.fe_add:
            if isinstance(fe, Edge) and fe.group is group:
                for edge in self.model.get_edges(group):
                    if edge in self.fe_remove:
                        continue
                    point = edge.intersect_edge(fe)
                    if point is None:
                        continue
                    if abs(point - edge.v1) > 2 * EPSILON and abs(point - edge.v2) > 2 * EPSILON:
                        self._remove_edge_and_add_copy(edge)
        #
        # find pairs (fe, edge), where the 'edge' cuts 'fe' in two
        progress = False
        all_edges = self._all_active_edges(group)
        for i, fe in enumerate(self.fe_add):
            if isinstance(fe, Edge) and fe.group is group:
                for edge in all_edges:
                    point = edge.intersect_edge(fe)
                    if point is None:
                        continue
                    if abs(point - fe.v1) > 2 * EPSILON and abs(point - fe.v2) > 2 * EPSILON:
                        del self.fe_add[i]
                        fe1 = Edge(group, fe.v1, point)
                        fe2 = Edge(group, point, fe.v2)
                        self.fe_add.append(fe1)
                        self.fe_add.append(fe2)
                        for fef in self.fe_add:
                            if isinstance(fef, Face):
                                try:
                                    index = fef.edges.index(fe)
                                except ValueError:
                                    pass
                                else:
                                    fef.edges[index] = fe1
                                    fef.edges.insert(index + 1, fe2)
                        progress = True
        return progress

    def consolidate_subdivide_edges(self):
        progress = False
        for group in self._all_changed_groups():
            progress |= self.consolidate_subdivide_edges_group(group)
        return progress

    def _consolidate_subdivide_face(self, face, edge):
        assert face.group is edge.group
        if face in self.fe_remove or edge in self.fe_remove:
            return False
        if not edge.in_plane(face.plane):
            return False
        face_vertices = [e.v1 for e in face.edges]
        try:
            i1 = face_vertices.index(edge.v1)
        except ValueError:
            i1 = -1
        try:
            i2 = face_vertices.index(edge.v2)
        except ValueError:
            i2 = -1
        if i1 < 0 and i2 < 0:
            return False
        if i1 >= 0 and i2 >= 0 and abs(i1 - i2) in [0, 1, len(face_vertices) - 1]:
            return False

        if i1 >= 0:
            current_branch = [edge.v1, edge.v2]
        else:
            current_branch = [edge.v2, edge.v1]
        middle = (edge.v1 + edge.v2) * 0.5
        if not face.point_is_inside(middle):
            return False
        for e in face.edges:
            if e.point_is_inside(middle):
                return False
        seen_points = GeometryDict()
        all_edges = self._all_active_edges(face.group)
        choices = []

        while True:
            head = current_branch[-1]
            if head in face_vertices:
                break   # connecting back!
            seen_points[head] = True

            tails = []
            v_step = head - current_branch[-2]
            v_ortho = v_step.cross(face.plane.normal)

            def see(v):
                if v not in seen_points and face.plane.distance_to_point(v) < EPSILON:
                    if len(current_branch) == 2 and v == current_branch[0]:
                        return
                    v_next = v - head
                    y = v_step.dot(v_next)
                    x = v_ortho.dot(v_next)
                    tails.append((math.atan2(x, y), v))

            for e in all_edges:
                if e.v1 == head:
                    see(e.v2)
                elif e.v2 == head:
                    see(e.v1)
            tails.sort()

            while not tails:
                if not choices:
                    return False    # did not manage to connect back
                tails = choices.pop()
                current_branch.pop()

            choices.append(tails)
            _, next_head = tails.pop()
            current_branch.append(next_head)

        # we can split the face in two along the points in 'current_branch',
        # which is a list of points starting at a vertex of 'face', and ending
        # at a (generally different) vertex of 'face'.
        i1 = face_vertices.index(current_branch[0])
        i2 = face_vertices.index(current_branch[-1])
        edges1 = []
        edges2 = []
        target = edges1
        i = i1
        for _ in range(len(face.edges)):
            if i == i2:
                target = edges2
            target.append(face.edges[i])
            i = (i + 1) % len(face.edges)

        for k in range(len(current_branch) - 1, 0, -1):
            edges1.append(self.add_edge(face.group, current_branch[k], current_branch[k - 1]))

        for k in range(len(current_branch) - 1):
            edges2.append(self.add_edge(face.group, current_branch[k], current_branch[k + 1]))

        self.fe_remove.add(face)
        self.add_face(edges1)
        self.add_face(edges2)
        return True

    def consolidate_subdivide_faces_group(self, group):
        progress = False
        all_faces = self._all_active_faces(group)
        all_edges = self._all_active_edges(group)
        for fe in self.fe_add:
            if fe.group is not group:
                continue
            if isinstance(fe, Edge):
                for face in all_faces:
                    progress |= self._consolidate_subdivide_face(face, fe)
            elif isinstance(fe, Face):
                for edge in all_edges:
                    progress |= self._consolidate_subdivide_face(fe, edge)
        return progress

    def consolidate_subdivide_faces(self):
        progress = False
        for group in self._all_changed_groups():
            progress |= self.consolidate_subdivide_faces_group(group)
        #
        # normalize: kill faces that are both added and removed
        if progress:
            add_remain = []
            for fe in self.fe_add:
                if fe in self.fe_remove:
                    self.fe_remove.remove(fe)
                else:
                    add_remain.append(fe)
            self.fe_add = add_remain
        return progress

    def consolidate(self, app):
        #self._dump()

        # - remove zero-length edges, and zero-edges faces
        self.consolidate_temporary()

        # - subdivide edges if there are new edges that cross them in the middle
        while self.consolidate_subdivide_edges():
            pass

        # - subdivide faces if there are new edges in the middle of them
        while self.consolidate_subdivide_faces():
            pass

        # - remove duplicate edges and faces
        # XXX NOT IMPLEMENTED YET

        self.check_valid()

        # - remove empty groups
        for key, value in self.model.group_edges.items():
            if len(value) == 0:
                del self.model.group_edges[key]
        for key, value in self.model.group_faces.items():
            if len(value) == 0:
                del self.model.group_faces[key]

        #self._dump()

    def check_valid(self):
        # - assert that all the edges of the faces are present in the same group
        group_edges = {}
        for fe in self.fe_add:
            if isinstance(fe, Face):
                try:
                    all_edges = group_edges[fe.group]
                except KeyError:
                    all_edges = group_edges[fe.group] = self._all_active_edges(fe.group)
                for edge in fe.edges:
                    assert edge in all_edges
        # - assert that we don't remove anything not present
        for fe in self.fe_remove:
            if isinstance(fe, Face):
                assert fe in self.model.get_faces(fe.group)
            elif isinstance(fe, Edge):
                assert fe in self.model.get_edges(fe.group)
            else:
                raise TypeError(type(fe))
        # - assert that we don't add something already there
        for fe in self.fe_add:
            if isinstance(fe, Face):
                assert fe not in self.model.get_faces(fe.group)
            elif isinstance(fe, Edge):
                assert fe not in self.model.get_edges(fe.group)
            else:
                raise TypeError(type(fe))

    _DUMP_NEXT = 0
    def _dump(self):
        filename = 'dump%d.txt' % ModelStep._DUMP_NEXT
        ModelStep._DUMP_NEXT += 1
        with open(filename, 'w') as f:
            print >> f, 'Remove:'
            for fe in self.fe_remove:
                print >> f, repr(fe)
            print >> f
            print >> f, 'Add:'
            for fe in self.fe_add:
                print >> f, repr(fe)
