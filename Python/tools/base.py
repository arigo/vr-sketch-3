DISTANCE_MOVEMENT_MIN = 0.05
DISTANCE_MOVEMENT_TIME = 0.4


class BaseTool(object):
    KEEP_SELECTION = False
    CANCEL_WHEN_NO_CONTROLLER = True
    GRAY_OUT_SUBGROUPS = False

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

    def unselect_now(self):
        pass


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
        if not self.KEEP_SELECTION and self.app.selected_edges:
            self.app.selected_edges.clear()
            self.app.selection_updated()

        self._all_controllers = controllers
        if self._clicking_gen is None:
            ctrl = self.handle_hover(controllers)
            self._following(ctrl)

        elif self._follow_ctrl not in controllers:
            if controllers or self.CANCEL_WHEN_NO_CONTROLLER:
                self.cancel()

        else:
            try:
                self._clicking_gen.next()
            except StopIteration:
                self._clicking_gen = None
                continue_tracking = self.handle_accept()
                if continue_tracking:
                    self._following(self._follow_ctrl)
            else:
                other_ctrl = self.other_ctrl(self._follow_ctrl, controllers)
                self.handle_drag(self._follow_ctrl, other_ctrl)

    def _following(self, ctrl):
        if ctrl is not None:
            self._follow_ctrl = ctrl
            self._clicking_gen = self._clicking(ctrl)

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
            # we wait for the next trigger-press to stop.  We accept trigger-presses from the
            # other controller, too.
            while True:
                yield
                if follow_ctrl not in self._all_controllers:
                    return
                for ctrl in self._all_controllers:
                    if ctrl.is_trigger_down():
                        return


class BaseTemporaryTool(BaseTool):
    CANCEL_WHEN_NO_CONTROLLER = False

    def _wait_for_next_click(self, follow_ctrl):
        while follow_ctrl.is_trigger_down():
            yield
        while True:
            if follow_ctrl not in self._all_controllers:
                return
            for ctrl in self._all_controllers:
                if ctrl.is_trigger_down():
                    return
            yield

    def enable_temporary_tool(self, ctrl):
        self._follow_ctrl = ctrl
        self._clicking_gen = self._wait_for_next_click(ctrl)
        return True

    def handle_hover(self, controllers):
        tool = self.app.ctrlmgr.unset_temporary_tool()
        tool.handle_controllers(controllers)
