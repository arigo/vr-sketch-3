from worldobj import ColoredPolygon, RectanglePointer, Cylinder, CrossPointer, DashedStem
from worldobj import TextHint, distance2text
from util import Vector3, WholeSpace, EmptyIntersection, Plane, SinglePoint
from model import EPSILON, ModelStep
import selection
from .base import BaseTool


class Rectangle(BaseTool):

    def __init__(self, app):
        BaseTool.__init__(self, app)
        self.fixed_direction = "y"

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position)
            if isinstance(closest, selection.SelectVoid):
                self.app.flash(RectanglePointer(ctrl.position))
            else:
                closest.flash(selection.HoverColorScheme)

            if ctrl.trigger_pressed():
                # start
                self.initial_selection = closest
                self.rectangle = None
                return ctrl

        return None

    def handle_accept(self):
        if self.rectangle:
            step = ModelStep(self.app.model, "Rectangle")
            e_list = []
            for i in range(len(self.rectangle)):
                e_list.append(step.add_edge(self.rectangle[i - 1], self.rectangle[i]))
            step.add_face(e_list)
            self.app.execute_step(step)

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        # Compute the target "selection" object from what we hover over
        closest = selection.find_closest(self.app, follow_ctrl.position)

        # Start computing the affine subspace for alignments
        subspace = closest.get_subspace()
        if isinstance(subspace, WholeSpace):
            p1 = self.initial_selection.get_point()
            diff = closest.get_point() - p1
            snap = diff.closest_axis_plane(selection.DISTANCE_VERTEX_MIN)
            if snap is not None:
                subspace = Plane.from_point_and_normal(p1, Vector3.from_axis(snap))
                
        # Factor in the other controller's position
        selection_guide = None
        if other_ctrl is not None:
            closest2 = selection.find_closest(self.app, other_ctrl.position)
            if not isinstance(closest2.get_subspace(), SinglePoint):
                if abs(other_ctrl.position - self.initial_selection.get_point()) < selection.DISTANCE_VERTEX_MIN:
                    closest2 = selection.SelectVertex(self.app, self.initial_selection.get_point())
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

        # Shift the target position to the alignment subspace
        closest.adjust(subspace.project_point_inside(closest.get_point()))

        # Draw the initial and final point
        self.initial_selection.flash(selection.SelectedColorScheme)
        closest.flash(selection.TargetColorScheme)

        if selection_guide:
            # Flash a dashed line to show that we have used the guide
            self.app.flash(DashedStem(selection_guide.get_point(), closest.get_point(),
                                        selection_guide_colors[0], selection_guide_colors[1]))

        # Build the rectangle based on these two points
        p1 = self.initial_selection.get_point()
        p3 = closest.get_point()

        dx = abs(p1.x - p3.x)
        dy = abs(p1.y - p3.y)
        dz = abs(p1.z - p3.z)
        if dx < EPSILON:
            self.fixed_direction = "y" if dy > dz else "z"
        elif dy < EPSILON:
            self.fixed_direction = "x" if dx > dz else "z"
        elif dz < EPSILON:
            self.fixed_direction = "x" if dx > dy else "y"

        p2 = p1.withcoord(self.fixed_direction, getattr(p3, self.fixed_direction))
        p4 = p3.withcoord(self.fixed_direction, getattr(p1, self.fixed_direction))
        self.rectangle = [p1, p2, p3, p4]

        #self.app.flash(Cylinder(p1, p2, selection.SelectedColorScheme.EDGE_AXIS[self.fixed_direction]))
        self.app.flash(Cylinder(p1, p2, selection.SelectedColorScheme.EDGE))
        self.app.flash(ColoredPolygon(self.rectangle, selection.TargetColorScheme.FACE))

        self.app.flash(TextHint(p1, p2, distance2text(abs(p2 - p1))))
        self.app.flash(TextHint(p1, p4, distance2text(abs(p4 - p1))))