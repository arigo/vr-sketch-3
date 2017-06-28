from worldobj import MovePointer, DashedStem, CrossPointer
from util import Vector3, WholeSpace, EmptyIntersection, Plane, SinglePoint
from model import EPSILON, UndoMove
import selection
from .base import BaseTool


class Move(BaseTool):

    def __init__(self, app):
        BaseTool.__init__(self, app)

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position)
            if isinstance(closest, selection.SelectVoid):
                self.app.flash(MovePointer(ctrl.position))
                continue
            closest.flash(selection.BluishHoverColorScheme)
            if ctrl.trigger_pressed():
                return self.start_movement(ctrl, closest)    # start
        return None

    def handle_cancel(self):
        self.undo.undo(self.app, self.app.model)

    def handle_accept(self):
        self.app.record_undoable_action(self.undo)

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        self.handle_cancel()

        # Compute the target "selection" object from what we hover over
        closest = selection.find_closest(self.app, follow_ctrl.position)

        # Must be within the allowed subspace
        subspace = self.subspace
        try:
            subspace = subspace.intersect(closest.get_subspace())
        except EmptyIntersection:
            closest = selection.SelectVoid(self.app, closest.get_point())

        # Try to match the initial_selection's guides
        original_stem_color = (0x202020,)
        best_guide = None
        best_guide_distance = (3, 0)
        for col1, col2, guide in self.initial_selection_guides:
            guide_distance = guide.selection_distance(self.app, closest.get_point())
            if guide_distance[1] > 1.0:
                continue
            if guide_distance < best_guide_distance:
                best_guide_distance = guide_distance
                best_guide = guide
                selection_guide_colors = col1, col2
        if best_guide is not None:
            try:
                subspace = subspace.intersect(best_guide)
            except EmptyIntersection:
                pass
            else:
                original_stem_color = selection_guide_colors

        # Factor in the other controller's position
        # XXX this part is almost a duplicate of the corresponding part from 'rectangle.py'
        selection_guides = []
        if other_ctrl is not None:
            closest2 = selection.find_closest(self.app, other_ctrl.position)
            self.app.flash(CrossPointer(closest2.get_point()))

            # Get the "guides" from the other controller's selection, which are
            # affine subspaces, and find if one of the vertices we're moving is
            # close to them
            for mv in self.move_vertices:
                best_guide = None
                best_guide_distance = (3, 0)
                for col1, col2, guide in closest2.alignment_guides():
                    guide_distance = guide.selection_distance(self.app, closest.get_point() + mv.delta)
                    if guide_distance[1] > 1.0:
                        continue
                    if guide_distance < best_guide_distance:
                        best_guide_distance = guide_distance
                        best_guide = guide
                        # this lambda is used to make a DashedStem instance with the current value of the
                        # variables *except* closest, which will take the adjusted value from later
                        make_dashed_stem = (lambda closest2=closest2, mv=mv, col1=col1, col2=col2:
                                            DashedStem(closest2.get_point(), closest.get_point() + mv.delta, col1, col2))
                if best_guide is not None:
                    try:
                        subspace = subspace.intersect(best_guide.shifted(-mv.delta))
                    except EmptyIntersection:
                        pass
                    else:
                        selection_guides.append(make_dashed_stem)

        # Shift the target position to the alignment subspace
        closest.adjust(subspace.project_point_inside(closest.get_point()))

        # Draw a dashed line from the initial to the final point
        self.app.flash(DashedStem(self.source_position, closest.get_point(),
                                  *original_stem_color))

        for make_dashed_stem in selection_guides:
            # Flash a dashed line to show that we have used the guide
            self.app.flash(make_dashed_stem())

        # Actually move the vertex
        for mv in self.move_vertices:
            mv.vertex.position = closest.get_point() + mv.delta
        self.undo.refresh(self.app, self.app.model)


    def start_movement(self, ctrl, closest):
        move_vertices = set(closest.individual_vertices())
        if not move_vertices:
            return None

        # compute the subspace inside which it's ok to move: we must not make any 
        # existing face non-planar
        subspace = WholeSpace()

        for face in self.app.model.faces:
            for edge in face.edges:
                if edge.v1 in move_vertices:
                    break
            else:
                continue     # none of the move_vertices belong to this face

            # check if we move that point completely off the current face's plane,
            # would the place stay planar?
            vertices = []
            for edge in face.edges:
                position = edge.v1.position
                if edge.v1 in move_vertices:
                    position += face.plane.normal * 100
                vertices.append(position)
            plane = Plane.from_vertices(vertices)

            for position in vertices:
                if plane.distance_to_point(position) > EPSILON:
                    # no => can't move off 'face.plane', then
                    try:
                        subspace = subspace.intersect(face.plane)
                    except EmptyIntersection:
                        return None
                    break

        self.source_position = closest.get_subspace().project_point_inside(ctrl.position)
        self.undo = UndoMove(move_vertices)
        self.move_vertices = [MoveVertex(v, self.source_position) for v in move_vertices]
        self.initial_selection_guides = (list(closest.alignment_guides()) + 
                                         list(selection.all_45degree_guides(self.source_position)))
        self.subspace = subspace
        return ctrl


class MoveVertex(object):
    def __init__(self, vertex, source_position):
        self.vertex = vertex
        self.delta = vertex.position - source_position
