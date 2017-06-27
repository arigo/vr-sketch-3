DISTANCE_MOVEMENT_MIN = 0.05
DISTANCE_MOVEMENT_TIME = 0.4


class BaseTool(object):

    def __init__(self, app):
        self.app = app
        self._clicking_gen = None

    def cancel(self):
        if self._clicking_gen is not None:
            try:
                self._clicking_gen.throw(GeneratorExit)
            except GeneratorExit:
                pass
            self._clicking_gen = None
            self.handle_cancel()


    # ----- methods to override -----

    def handle_hover(self, controllers):
        raise NotImplementedError

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        raise NotImplementedError

    def handle_accept(self):
        pass

    def handle_cancel(self):
        pass


    # ----- internal logic -----

    def other_ctrl(self, follow_ctrl, controllers):
        for ctrl in controllers:
            if ctrl is not follow_ctrl:
                return ctrl
        return None

    def handle_controllers(self, controllers):
        if self._clicking_gen is None:
            ctrl = self.handle_hover(controllers)
            if ctrl is not None:
                self._follow_ctrl = ctrl
                self._clicking_gen = self._clicking(ctrl)

        elif self._follow_ctrl not in controllers:
            self.cancel()

        else:
            try:
                self._clicking_gen.next()
            except StopIteration:
                self._clicking_gen = None
                self.handle_accept()
            else:
                other_ctrl = self.other_ctrl(self._follow_ctrl, controllers)
                self.handle_drag(self._follow_ctrl, other_ctrl)

    def _clicking(self, follow_ctrl):
        # detect movements or release of the trigger to distinguish between two modes:
        # we can either click and drag with the trigger, or click and release in-place
        # and then move the controller without holding down the trigger.

        app = self.app
        start_time = app.current_time
        initial_ctrl_position = follow_ctrl.position

        while follow_ctrl.is_trigger_down():
            if (abs(initial_ctrl_position - follow_ctrl.position) > app.scale_ctrl(DISTANCE_MOVEMENT_MIN)
                and app.current_time - start_time > DISTANCE_MOVEMENT_TIME):
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
