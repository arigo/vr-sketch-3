from worldobj import MovePointer, DashedStem, CrossPointer
from util import Vector3, WholeSpace, EmptyIntersection, Plane, SinglePoint
from model import EPSILON
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
        self.move_vertex_to(self.original_position)

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        # Compute the target "selection" object from what we hover over
        closest = selection.find_closest(self.app, follow_ctrl.position,
                                            ignore = self.initial_selection.vertex)

        # Must be within the allowed subspace
        subspace = self.subspace
        try:
            subspace = subspace.intersect(closest.get_subspace())
        except EmptyIntersection:
            closest = selection.SelectVoid(closest.get_point())

        # Shift the target position to the alignment subspace
        closest.adjust(subspace.project_point_inside(closest.get_point()))

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
        selection_guide = None
        if other_ctrl is not None:
            closest2 = selection.find_closest(self.app, other_ctrl.position)
            self.app.flash(CrossPointer(closest2.get_point()))

            # Get the "guides" from the other controller's selection, which are
            # affine subspaces, and find if we're close to one of them
            best_guide = None
            best_guide_distance = (3, 0)
            for col1, col2, guide in closest2.alignment_guides():
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
                    selection_guide = closest2

        # Shift again the target position to the alignment subspace
        closest.adjust(subspace.project_point_inside(closest.get_point()))

        # Draw a dashed line from the initial to the final point
        self.app.flash(DashedStem(self.original_position, closest.get_point(),
                                  *original_stem_color))

        if selection_guide:
            # Flash a dashed line to show that we have used the guide
            self.app.flash(DashedStem(selection_guide.get_point(), closest.get_point(),
                                        selection_guide_colors[0], selection_guide_colors[1]))

        # Actually move the vertex
        self.move_vertex_to(closest.get_point())

    def move_vertex_to(self, position):
        self.initial_selection.vertex.position = position
        for upd in self.update_display:
            self.app.display(upd)

    def start_movement(self, ctrl, closest):
        assert isinstance(closest, selection.SelectVertex), "XXX"

        # compute the subspace inside which it's ok to move: we must not make any 
        # existing face non-planar
        subspace = WholeSpace()
        update_display = []

        for face in self.app.model.faces:
            if face.find_vertex(closest.vertex) < 0:
                continue
            
            update_display.append(face)
            update_display.extend(face.edges)

            # check if we move that point completely off the current face's plane,
            # would the place stay planar?
            vertices = []
            for edge in face.edges:
                position = edge.v1.position
                if edge.v1 is closest.vertex:
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

        self.initial_selection = closest
        self.initial_selection_guides = list(self.initial_selection.alignment_guides())
        self.update_display = update_display
        self.subspace = subspace
        self.original_position = closest.vertex.position
        return ctrl