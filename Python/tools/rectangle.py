from worldobj import ColoredPolygon, RectanglePointer, Cylinder, CrossPointer, DashedStem
from util import Vector3, WholeSpace, EmptyIntersection, Plane
from model import EPSILON
import selection


DISTANCE_MOVEMENT_MIN = 0.05


class Rectangle(object):

    def __init__(self, app):
        self.app = app
        self.model = app.model
        self.clicking_gen = None
        self.fixed_direction = "y"

    def cancel(self):
        if self.clicking_gen is not None:
            self.clicking_gen.throw(GeneratorExit)
            self.clicking_gen = None

    def other_ctrl(self, controllers):
        for ctrl in controllers:
            if ctrl is not self.follow_ctrl:
                return ctrl
        return None

    def handle_controllers(self, controllers):
        if self.clicking_gen is None:

            for ctrl in controllers:
                closest = selection.find_closest(self.app, ctrl.position)
                if isinstance(closest, selection.SelectVoid):
                    self.app.flash(RectanglePointer(closest.position))
                else:
                    closest.flash(selection.HoverColorScheme)

                if ctrl.trigger_pressed():
                    # start
                    self.follow_ctrl = ctrl
                    self.initial_selection = closest
                    self.rectangle = None
                    self.clicking_gen = self.clicking(ctrl.position)
                    break

        elif self.follow_ctrl not in controllers:
            self.cancel()

        else:
            try:
                self.clicking_gen.next()
            except StopIteration:
                self.clicking_gen = None
                if self.rectangle:
                    self.app.model.new_face_from_vertices(self.app, self.rectangle)
            else:
                # Compute the target "selection" object from what we hover over
                closest = selection.find_closest(self.app, self.follow_ctrl.position)

                # Start computing the affine subspace for alignments
                subspace = WholeSpace()
                if isinstance(closest, selection.SelectVoid):
                    p1 = self.initial_selection.get_point()
                    diff = closest.get_point() - p1
                    snap = diff.closest_axis_plane(selection.DISTANCE_VERTEX_MIN)
                    if snap is not None:
                        subspace = Plane.from_point_and_normal(p1, Vector3.from_axis(snap))
                
                # Factor in the other controller's position
                selection_guide = None
                ctrl = self.other_ctrl(controllers)
                if ctrl is not None:
                    closest2 = selection.find_closest(self.app, ctrl.position)
                    self.app.flash(CrossPointer(closest2.get_point()))

                    # Get the "guides" from the other controller's selection, which are
                    # affine subspaces, and find if we're close to one of them
                    best_guide = None
                    best_guide_distance = (3, 0)
                    for guide in closest2.alignment_guides():
                        guide_distance = guide.selection_distance(self.app, closest.get_point())
                        if guide_distance[1] > 1.0:
                            continue
                        if guide_distance < best_guide_distance:
                            best_guide_distance = guide_distance
                            best_guide = guide
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
                                              selection.GuideColorScheme.EDGE))

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

                self.app.flash(Cylinder(p1, p2, selection.SelectedColorScheme.EDGE))
                self.app.flash(ColoredPolygon(self.rectangle, selection.TargetColorScheme.FACE))
                

    def clicking(self, initial_ctrl_position):
        # detect movements or release of the trigger to distinguish between two modes:
        # we can either click and drag with the trigger, or click and release in-place
        # and then move the controller without holding down the trigger.

        app = self.app
        follow_ctrl = self.follow_ctrl
        while follow_ctrl.is_trigger_down():
            if abs(initial_ctrl_position - follow_ctrl.position) > app.scale_ctrl(DISTANCE_MOVEMENT_MIN):
                # we moved far enough and the trigger is still down.  Switch to a mode where we
                # follow as long as the trigger is down, and stop when it is released.
                while follow_ctrl.is_trigger_down():
                    yield
                break
            yield
        else:
            # we released the trigger before moving the controller away.  Switch to a mode where
            # we wait for the next trigger-press to stop.
            while not follow_ctrl.is_trigger_down():
                yield
