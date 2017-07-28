from worldobj import PencilPointer, Stem, DashedStem, CrossPointer, PolygonHighlight
from worldobj import TextHint, distance2text
from util import Vector3, WholeSpace, EmptyIntersection, Plane, SinglePoint
from model import EPSILON, ModelStep
import selection, face_reduction
from .base import BaseTool


class Line(BaseTool):

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position, only_group=self.app.curgroup)
            self.app.flash(PencilPointer(closest.get_point(), ctrl))

            new_vertices = None
            if isinstance(closest, selection.SelectVoid):
                new_vertices = face_reduction.potential_new_face(self.app.model, self.app.curgroup,
                                                                 closest.get_point(),
                                                                 max_distance = 0.95 * selection.DISTANCE_FACE_MIN)
                if new_vertices is not None:
                    self.app.flash(PolygonHighlight(new_vertices, color = selection.TargetColorScheme.FACE))

            if ctrl.trigger_pressed():
                if new_vertices is None:
                    self.initial_selection = closest
                    self.source_position = closest.get_point()
                    self.target_position = self.source_position
                    self.fixed_distance = None
                    return ctrl
                else:
                    self.action_new_face(new_vertices)
                    return None
        return None

    def handle_accept(self):
        if self.source_position != self.target_position:
            step = ModelStep(self.app.model, "Draw line")
            step.add_edge(self.app.curgroup, self.source_position, self.target_position)
            self.app.execute_step(step)

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        # Compute the target "selection" object from what we hover over
        closest = selection.find_closest(self.app, follow_ctrl.position)

        # Start computing the affine subspace for alignments
        subspace = closest.get_subspace()

        # Get the "guides" from the initial selection, which are
        # affine subspaces, and find if we're close to one of them
        selection_guide_1 = None
        best_guide = None
        best_guide_distance = (3, 0)
        for col1, col2, guide in (list(self.initial_selection.alignment_guides()) +
                                  list(selection.all_45degree_guides(self.source_position))):
            guide_distance = guide.selection_distance(self.app, closest.get_point())
            if guide_distance[1] > 1.0:
                continue
            if guide_distance < best_guide_distance:
                best_guide_distance = selection.marginal_increase(guide_distance)
                best_guide = guide
                selection_guide_colors_1 = col1, col2
        if best_guide is not None:
            try:
                subspace = subspace.intersect(best_guide)
            except EmptyIntersection:
                pass
            else:
                selection_guide_1 = self.initial_selection

        # Factor in the other controller's position
        selection_guide = None
        if other_ctrl is not None:
            closest2 = selection.find_closest(self.app, other_ctrl.position)
            if not isinstance(closest2.get_subspace(), SinglePoint):
                if abs(other_ctrl.position - self.source_position) < selection.DISTANCE_VERTEX_MIN:
                    closest2 = selection.SelectVertex(self.app, self.source_position)
            self.app.flash(CrossPointer(closest2.get_point(), other_ctrl))

            # Get the "guides" from the other controller's selection, which are
            # affine subspaces, and find if we're close to one of them
            best_guide = None
            best_guide_distance = (3, 0)
            for col1, col2, guide in closest2.alignment_guides():
                guide_distance = guide.selection_distance(self.app, closest.get_point())
                if guide_distance[1] > 1.0:
                    continue
                if guide_distance < best_guide_distance:
                    best_guide_distance = selection.marginal_increase(guide_distance)
                    best_guide = guide
                    selection_guide_colors = col1, col2
            if best_guide is not None:
                try:
                    subspace = subspace.intersect(best_guide)
                except EmptyIntersection:
                    pass
                else:
                    selection_guide = closest2

        # Shift the target position to the alignment subspace
        p3 = subspace.project_point_inside(closest.get_point())

        # Apply the fixed distance, if any
        if self.fixed_distance is not None:
            length1 = abs(self.source_position - p3)
            if length1 > EPSILON:
                p3 = self.source_position + (p3 - self.source_position) * (self.fixed_distance / length1)

        if selection_guide_1:
            # Flash a dashed line to show that we have used the guide
            self.app.flash(DashedStem(selection_guide_1.get_point(), p3,
                                      selection_guide_colors_1[0], selection_guide_colors_1[1]))
        if selection_guide:
            # Flash a dashed line to show that we have used the guide
            self.app.flash(DashedStem(selection_guide.get_point(), p3,
                                      selection_guide_colors[0], selection_guide_colors[1]))

        closest.adjust(p3)

        # Draw the new edge
        p1 = self.source_position
        p2 = self.target_position = closest.get_point()
        self.app.flash(Stem(p1, p2, selection.TargetColorScheme.DARKER_EDGE))

        # Add the distance hint
        controller_num = self._all_controllers.index(follow_ctrl)
        token = self.app.fetch_manual_token(self, "length")
        self.app.flash(TextHint(p1, p2, distance2text(abs(p2 - p1)), controller_num, token))

    def manual_enter(self, key, new_value):
        assert key == "length"
        self.fixed_distance = new_value

    def action_new_face(self, new_vertices):
        step = ModelStep(self.app.model, "Draw face")
        step.add_face([step.add_edge(self.app.curgroup, new_vertices[i - 1], new_vertices[i]) for i in range(len(new_vertices))])
        self.app.execute_step(step)
