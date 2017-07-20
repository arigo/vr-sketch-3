import worldobj
from util import Vector3

PRESS_TRIGGER  = 1
PRESS_GRIP     = 2
PRESS_TOUCHPAD = 4


class Controller(object):

    def __init__(self, index):
        self._index = index

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

    def show_menu(self, items):
        # _show_menu() is injected into the globals by app.initialize_functions()
        s = '\n'.join(['%s:%s' % (id, text) for (id, text) in items])
        _show_menu(self._index, s)


class ControllersMgr(object):
    TOOLS = ["select", "eraser", "line", "rectangle", "pushpull", "move"]
    TOOL_NAMES = {"line": "Draw Line/Face",
                  "pushpull": "Push/Pull"}

    def __init__(self, app):
        self.app = app
        self.controllers = []
        self.tool = None
        self.load_tool("rectangle")

    def load_tool(self, name):
        module = __import__("tools.%s" % name, None, None, [name])
        ToolCls = getattr(module, name.capitalize())
        if self.tool is not None:
            self.tool.cancel()
        self.tool = ToolCls(self.app)
        self.selected_tool = name

    def handle_controllers(self, num_controllers, controllers):
        if len(self.controllers) != num_controllers:
            while len(self.controllers) > num_controllers:
                self.controllers.pop()
            while len(self.controllers) < num_controllers:
                self.controllers.append(Controller(len(self.controllers)))

        for i in range(num_controllers):
            cpos = Vector3(controllers[i * 4],
                           controllers[i * 4 + 1],
                           controllers[i * 4 + 2])
            pressed = int(controllers[i * 4 + 3])
            self.controllers[i].update(cpos, pressed)

        self.app.model_scale = controllers[num_controllers * 4]
        self.app.current_time = controllers[num_controllers * 4 + 1]

        # this shows the tool selection menu when we press the touchpad, for now.
        # Once a menu is active, C# will call this function with num_controllers == 0,
        # which cancels the tool-specific action, hides cursors, etc.
        for ctrl in self.controllers:
            if ctrl.pressed & ~ctrl.prev_pressed & PRESS_TOUCHPAD:
                ctrl.show_menu(self.get_tools_menu())
                return

        # this just adds a gray-black cylinder between the two controllers when both grips
        # are pressed; the actual logic for the grip button is in C#
        if len(self.controllers) >= 2:
            if self.controllers[0].pressed & self.controllers[1].pressed & PRESS_GRIP:
                #color = self.app.current_time % 1.0
                #if color > 0.5: color = 1.0 - color
                #color = int(300 * color) * 0x010101
                color = 0x404040
                self.app.flash(worldobj.Cylinder(
                    self.controllers[0].position, self.controllers[1].position, color=color))
                text = "%.2f x" % (self.app.model_scale,)
                self.app.flash(worldobj.TextHint(
                    self.controllers[0].position, self.controllers[1].position, text))

        self.tool.handle_controllers(self.controllers)

    def get_tools_menu(self):
        for tool_name in self.TOOLS:
            text = unicode(self.TOOL_NAMES.get(tool_name, tool_name.capitalize()))
            if tool_name == self.selected_tool:
                text = u"\u2714 " + text
            yield ('tool_' + tool_name, text)
        uactions = self.app.undoable_actions
        ractions = self.app.redoable_actions
        yield ('undo', 'Undo %s' % (uactions[-1].name if uactions else '(nothing)'))
        yield ('redo', 'Redo %s' % (ractions[-1].name if ractions else '(nothing)'))
