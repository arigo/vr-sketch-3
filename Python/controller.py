import worldobj
from util import Vector3

PRESS_TRIGGER = 1
PRESS_GRIP    = 2


class Controller(object):

    def update(self, pos, pressed):
        self.position = pos
        self.prev_pressed = getattr(self, 'pressed', pressed)
        self.pressed = pressed

    def trigger_pressed(self):
        return (self.pressed & ~self.prev_pressed) & PRESS_TRIGGER

    def trigger_released(self):
        return (~self.pressed & self.prev_pressed) & PRESS_TRIGGER

    def is_trigger_down(self):
        return self.pressed & PRESS_TRIGGER


class ControllersMgr(object):
    tool = None

    def __init__(self, app):
        self.app = app
        self.controllers = []
        self.load_tool("Rectangle")

    def load_tool(self, name):
        module = __import__("tools.%s" % (name.lower(),), None, None, [name])
        ToolCls = getattr(module, name)
        if self.tool is not None:
            self.tool.cancel()
        self.tool = ToolCls(self.app)

    def handle_controllers(self, num_controllers, controllers):
        if len(self.controllers) != num_controllers:
            while len(self.controllers) > num_controllers:
                self.controllers.pop()
            while len(self.controllers) < num_controllers:
                self.controllers.append(Controller())

        for i in range(num_controllers):
            cpos = Vector3(controllers[i * 4],
                           controllers[i * 4 + 1],
                           controllers[i * 4 + 2])
            pressed = int(controllers[i * 4 + 3])
            self.controllers[i].update(cpos, pressed)

        self.app.model_scale = controllers[num_controllers * 4]

        # this just adds a black cylinder between the two controllers when both grips
        # are pressed; the actual logic for the grip button is in C#
        if len(self.controllers) >= 2:
            if self.controllers[0].pressed & self.controllers[1].pressed & PRESS_GRIP:
                self.app.flash(worldobj.Cylinder(
                    self.controllers[0].pos, self.controllers[1].pos, color=0x202020))

        self.tool.handle_controllers(self.controllers)
