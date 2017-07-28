from worldobj import MovePointer, DashedStem, CrossPointer
from worldobj import TextHint, distance2text
from util import Vector3, WholeSpace, EmptyIntersection, Plane, SinglePoint, GeometryDict
from model import EPSILON, ModelStep
import selection
from .base import BaseTool


class Move(BaseTool):
    KEEP_SELECTION = True

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position, only_group=self.app.curgroup)
            if isinstance(closest, selection.SelectVoid):
                self.app.flash(MovePointer(ctrl.position, ctrl))
                continue
            closest.flash(selection.BluishHoverColorScheme)
            if ctrl.trigger_pressed():
                return self.start_movement(ctrl, closest)    # start
        return None

    def handle_cancel(self):
        self.model_step.reversed().apply(self.app)

    def handle_accept(self):
        self.handle_cancel()
        self.app.execute_step(self.model_step)
        del self.model_step

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        self.handle_cancel()

        # Compute the target "selection" object from what we hover over,
        # ignoring the original 'move_vertices'
        closest = selection.find_closest(self.app, follow_ctrl.position,
                                         ignore=self.move_vertices)

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
                try:
                    try_subspace = subspace.intersect(guide)
                except EmptyIntersection:
                    pass
                else:
                    if isinstance(try_subspace, SinglePoint) and try_subspace.position == self.source_position:
                        continue
                    best_guide_distance = selection.marginal_increase(guide_distance)
                    best_guide = guide
                    best_subspace = try_subspace
                    selection_guide_colors = col1, col2
        if best_guide is not None:
            subspace = best_subspace
            original_stem_color = selection_guide_colors

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

        # Actually move the vertex
        delta = closest.get_point() - self.source_position
        old2new = [(v, v + delta) for v in self.move_vertices]
        
        if len(self.move_vertices) == 1:
            name = 'Move vertex'
        else:
            name = 'Move %d vertices' % (len(self.move_vertices),)
        self.model_step = ModelStep(self.app.model, name)
        self.model_step.move_vertices(old2new, self.move_edges, self.move_faces)
        self.app.execute_temporary_step(self.model_step)

        # Add the distance hint
        if p1 != p2:
            controller_num = self._all_controllers.index(follow_ctrl)
            token = self.app.fetch_manual_token(self, "length")
            self.app.flash(TextHint(p1, p2, distance2text(abs(p2 - p1)), controller_num, token))


    def manual_enter(self, key, new_value):
        assert key == "length"
        self.fixed_distance = new_value


    def start_movement(self, ctrl, closest):
        move_vertices = GeometryDict()
        for v in closest.individual_vertices():
            move_vertices[v] = True
        if not move_vertices:
            return None

        common_vertices = False
        for edge in self.app.selected_edges:
            common_vertices = common_vertices or edge.v1 in move_vertices or edge.v2 in move_vertices
        if common_vertices:
            for edge in self.app.selected_edges:
                move_vertices[edge.v1] = True
                move_vertices[edge.v2] = True

        self.move_vertices = move_vertices
        self.move_edges = set([edge for edge in self.app.getcuredges()
                                    if edge.v1 in move_vertices or edge.v2 in move_vertices])
        self.move_faces = []

        # compute the subspace inside which it's ok to move: we must not make any 
        # existing face non-planar
        self.source_position = closest.get_subspace().project_point_inside(ctrl.position)
        subspace = WholeSpace()

        for face in self.app.getcurfaces():
            for edge in face.edges:
                if edge in self.move_edges:
                    break
            else:
                continue     # none of the move_vertices belong to this face

            self.move_faces.append(face)

            # check if we move that point completely off the current face's plane,
            # would the place stay planar?
            vertices = []
            for edge in face.edges:
                position = edge.v1
                if edge.v1 in move_vertices:
                    position += face.plane.normal * 100
                vertices.append(position)
            plane = Plane.from_vertices(vertices)

            for position in vertices:
                if plane.distance_to_point(position) > EPSILON:
                    # no => can't move off 'face.plane', then
                    plane = Plane.from_point_and_normal(self.source_position, face.plane.normal)
                    try:
                        subspace = subspace.intersect(plane)
                    except EmptyIntersection:
                        return None
                    break

        self.initial_selection_guides = (list(closest.alignment_guides()) + 
                                         list(selection.all_45degree_guides(self.source_position)))
        self.subspace = subspace
        self.model_step = ModelStep(self.app.model, "No movement")
        self.fixed_distance = None
        return ctrl
