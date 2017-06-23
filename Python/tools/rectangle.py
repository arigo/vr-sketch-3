from worldobj import ColoredPolygon
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
                closest.flash(selection.HoverColorScheme)

                if ctrl.trigger_pressed():
                    # start
                    self.follow_ctrl = ctrl
                    self.clicking_gen = self.clicking(closest, ctrl.position)
                    break

        elif self.follow_ctrl not in controllers:
            self.cancel()

        else:
            self.controllers = controllers
            try:
                self.clicking_gen.next()
            except StopIteration:
                self.clicking_gen = None

    def clicking(self, initial, initial_ctrl_position):
        follow_release = -1
        follow_ctrl = self.follow_ctrl
        app = self.app

        while True:
            # detect releases of the trigger to distinguish between two modes:
            # we can either click and drag with the trigger (mode 'follow_release=1'),
            # or click and release in-place and then move the controller without holding
            # down the trigger (mode 'follow_release=0').  Initially, follow_release=-1.
            
            if follow_release == -1:
                if follow_ctrl.is_trigger_down():
                    # if we moved far enough and the trigger is still down, switch to follow_release=1
                    if abs(initial_ctrl_position - follow_ctrl.position) > app.scale_ctrl(DISTANCE_MOVEMENT_MIN):
                        follow_release = 1
                else:
                    # if we released the trigger without moving much, switch to follow_release=0
                    follow_release = 0
                    
            elif follow_release == 0:
                if follow_ctrl.trigger_pressed():
                    break

            elif follow_release == 1:
                if follow_ctrl.trigger_released():
                    break

            initial.flash(selection.SelectedColorScheme)
            closest = selection.find_closest(app, follow_ctrl.position)
            closest.flash(selection.TargetColorScheme)

            yield
