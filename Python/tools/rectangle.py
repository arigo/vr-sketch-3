from worldobj import ColoredPolygon, RectanglePointer
from util import Vector3
from model import EPSILON
import selection


DISTANCE_MOVEMENT_MIN = 0.05


class Rectangle(object):

    def __init__(self, app):
        self.app = app
        self.model = app.model
        self.clicking_gen = None

    def cancel(self):
        if self.clicking_gen is not None:
            self.clicking_gen.throw(GeneratorExit)
            self.clicking_gen = None

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
            self.controllers = controllers
            try:
                self.clicking_gen.next()
            except StopIteration:
                self.clicking_gen = None
                if self.rectangle:
                    self.app.model.new_face_from_vertices(self.app, self.rectangle)
            else:
                self.initial_selection.flash(selection.SelectedColorScheme)
                closest = selection.find_closest(self.app, self.follow_ctrl.position)
                if isinstance(closest, selection.SelectVoid):
                    closest.move_to_aligned_plane(self.initial_selection.get_point())
                closest.flash(selection.TargetColorScheme)

                p1 = self.initial_selection.get_point()
                p2 = closest.get_point()
                if abs(p1.y - p2.y) < EPSILON:
                    self.rectangle = [p1,
                                      Vector3(p1.x, p1.y, p2.z), 
                                      Vector3(p2.x, p1.y, p2.z),
                                      Vector3(p2.x, p1.y, p1.z)]
                else:
                    self.rectangle = [p1,
                                      Vector3(p1.x, p2.y, p1.z),
                                      p2,
                                      Vector3(p2.x, p1.y, p2.z)]
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
