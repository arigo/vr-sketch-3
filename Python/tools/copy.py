from worldobj import ColoredPolygon, Stem, DashedStem, CrossPointer
from worldobj import TextHint, distance2text
from util import Vector3, WholeSpace, EmptyIntersection, Plane, SinglePoint, GeometryDict
from model import EPSILON, ModelStep
import selection
from .base import BaseTemporaryTool


class Copy(BaseTemporaryTool):

    def enable_temporary_tool(self, ctrl):
        move_vertices = GeometryDict()
        for edge in self.app.selected_edges:
            move_vertices[edge.v1] = True
            move_vertices[edge.v2] = True
        if not move_vertices:
            return False

        move_edges = set([edge for edge in self.app.getcuredges()
                               if edge.v1 in move_vertices and edge.v2 in move_vertices])
        move_faces = [face for face in self.app.getcurfaces()
                           if all(e in move_edges for e in face.edges)]

        self.move_vertices = move_vertices
        self.move_edges = move_edges
        self.move_faces = move_faces

        dist = [(abs(v - self.app.head), v) for v in move_vertices]
        self.source_position = min(dist)[1]
        self.initial_selection_guides = list(selection.all_45degree_guides(self.source_position))
        self.delta = None
        self.fixed_distance = None

        return BaseTemporaryTool.enable_temporary_tool(self, ctrl)


    def handle_accept(self):
        delta = self.delta
        if delta:
            step = ModelStep(self.app.model, "Copy selection")
            e_dict = {}
            for edge in self.move_edges:
                e_dict[edge] = step.add_edge(edge.v1 + delta, edge.v2 + delta)
            for face in self.move_faces:
                step.add_face([e_dict[e] for e in face.edges])
            self.app.execute_step(step)


    def handle_drag(self, follow_ctrl, other_ctrl=None):
        # XXXXXXXX Huge Amount of Copy-Paste-Edit From move.py is Bad XXXXXXXX

        # Compute the target "selection" object from what we hover over
        closest = selection.find_closest(self.app, follow_ctrl.position)

        # Try to match the initial_selection's guides
        original_stem_color = (0x202020,)
        subspace = WholeSpace()
        best_guide_distance = (3, 0)
        for col1, col2, guide in self.initial_selection_guides:
            guide_distance = guide.selection_distance(self.app, closest.get_point())
            if guide_distance[1] > 1.0:
                continue
            if guide_distance < best_guide_distance:
                best_guide_distance = selection.marginal_increase(guide_distance)
                subspace = guide
                original_stem_color = col1, col2

        # Factor in the other controller's position
        # XXX this part is almost a duplicate of the corresponding part from 'rectangle.py'
        selection_guides = []
        if other_ctrl is not None:
            closest2 = selection.find_closest(self.app, other_ctrl.position)
            self.app.flash(CrossPointer(closest2.get_point(), other_ctrl))

            # Get the "guides" from the other controller's selection, which are
            # affine subspaces, and find if one of the vertices we're moving is
            # close to them
            for mv in self.move_vertices:
                delta = mv - self.source_position
                best_guide = None
                best_guide_distance = (3, 0)
                for col1, col2, guide in closest2.alignment_guides():
                    guide_distance = guide.selection_distance(self.app, closest.get_point() + delta)
                    if guide_distance[1] > 1.0:
                        continue
                    if guide_distance < best_guide_distance:
                        best_guide_distance = selection.marginal_increase(guide_distance)
                        best_guide = guide
                        # this lambda is used to make a DashedStem instance with the current value of the
                        # variables *except* closest, which will take the adjusted value from later
                        make_dashed_stem = (lambda closest2=closest2, delta=delta, col1=col1, col2=col2:
                                            DashedStem(closest2.get_point(), closest.get_point() + delta, col1, col2))
                if best_guide is not None:
                    try:
                        subspace = subspace.intersect(best_guide.shifted(-delta))
                    except EmptyIntersection:
                        pass
                    else:
                        selection_guides.append(make_dashed_stem)

        # Shift the target position to the alignment subspace
        p3 = subspace.project_point_inside(closest.get_point())

        # Apply the fixed distance, if any
        if self.fixed_distance is not None:
            length1 = abs(self.source_position - p3)
            if length1 > EPSILON:
                p3 = self.source_position + (p3 - self.source_position) * (self.fixed_distance / length1)

        closest.adjust(p3)

        # Draw a dashed line from the initial to the final point
        p1 = self.source_position
        p2 = closest.get_point()
        self.app.flash(DashedStem(p1, p2, *original_stem_color))

        for make_dashed_stem in selection_guides:
            # Flash a dashed line to show that we have used the guide
            self.app.flash(make_dashed_stem())

        # Add the distance hint
        if p1 != p2:
            controller_num = self._all_controllers.index(follow_ctrl)
            token = self.app.fetch_manual_token(self, "length")
            self.app.flash(TextHint(p1, p2, distance2text(abs(p2 - p1)), controller_num, token))

        # ----------

        delta = self.delta = p3 - self.source_position
        for edge in self.move_edges:
            self.app.flash(Stem(edge.v1 + delta, edge.v2 + delta,
                                selection.SelectedColorScheme.EDGE))
        for face in self.move_faces:
            self.app.flash(ColoredPolygon([e.v1 + delta for e in face.edges],
                                          selection.TargetColorScheme.FACE))


    def manual_enter(self, key, new_value):
        assert key == "length"
        self.fixed_distance = new_value
