import worldobj
from util import Vector3

PRESS_TRIGGER  = 1
PRESS_GRIP     = 2
PRESS_TOUCHPAD = 4


class Controller(object):

    def __init__(self, index):
        self._index = index

    def recreate(self):
        if hasattr(self, 'pressed'):
            del self.pressed

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

    def show_menu(self, items, force):
        # _show_menu() is injected into the globals by app.initialize_functions()
        s = u'\n'.join(['%s\t%s' % (id, text) for (id, text) in items])
        _show_menu(self._index + (1000 if force else 0), s)

    
class ControllersMgr(object):
    TOOLS = ["select", "eraser", "line", "rectangle", "pushpull", "move", "teleport"]
    TOOL_NAMES = {"line": "Draw Line/Face",
                  "pushpull": "Push/Pull"}

    def __init__(self, app):
        self.app = app
        self.controllers = []
        self.controllers_cache = {}
        self.tool = None
        self.load_tool("select")

    def load_tool(self, name):
        module = __import__("tools.%s" % name, None, None, [name])
        ToolCls = getattr(module, name.capitalize())
        if self.tool is not None:
            self.tool.cancel()
            self.tool.unselect_now()
        self.tool = ToolCls(self.app)
        self.selected_tool = name
        if self.app.gray_out_subgroups != self.tool.GRAY_OUT_SUBGROUPS:
            self.app.gray_out_subgroups = self.tool.GRAY_OUT_SUBGROUPS
            self.app.selection_updated()

    def set_temporary_tool(self, tool, ctrl):
        self.tool.cancel()
        if tool.enable_temporary_tool(ctrl):
            self.tool.unselect_now()
            self.tool = tool

    def unset_temporary_tool(self):
        self.load_tool(self.selected_tool)
        return self.tool

    def handle_controllers(self, num_controllers, controllers):
        if len(self.controllers) != num_controllers:
            while len(self.controllers) > num_controllers:
                self.controllers.pop()
            while len(self.controllers) < num_controllers:
                _index = len(self.controllers)
                if _index not in self.controllers_cache:
                    self.controllers_cache[_index] = Controller(_index)
                self.controllers_cache[_index].recreate()
                self.controllers.append(self.controllers_cache[_index])

        for i in range(num_controllers):
            cpos = Vector3(controllers[i * 4],
                           controllers[i * 4 + 1],
                           controllers[i * 4 + 2])
            pressed = int(controllers[i * 4 + 3])
            self.controllers[i].update(cpos, pressed)

        self.app.model_scale = controllers[num_controllers * 4]
        self.app.current_time = controllers[num_controllers * 4 + 1]
        self.app.head = Vector3(controllers[num_controllers * 4 + 2],
                                controllers[num_controllers * 4 + 3],
                                controllers[num_controllers * 4 + 4])

        # this shows the tool selection menu when we press the touchpad, for now.
        # Once a menu is active, C# will call this function with num_controllers == 0,
        # which cancels the tool-specific action, hides cursors, etc.
        for ctrl in self.controllers:
            if ctrl.pressed & ~ctrl.prev_pressed & PRESS_TOUCHPAD:
                self.app.current_menu_ctrl = ctrl
                ctrl.show_menu(self.get_tools_menu(), force=False)
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
            key = 'tool_' + tool_name
            text = unicode(self.TOOL_NAMES.get(tool_name, tool_name.capitalize()))
            if tool_name == self.selected_tool:
                if tool_name == 'select':
                    text = 'Select/Edit...'
                    key = 'edit'
                text = u"\u2714 " + text
            yield (key, text)
        uactions = self.app.file.undoable_actions
        ractions = self.app.file.redoable_actions
        yield ('undo', ('Undo %s' % uactions[-1].name) if uactions else '(Undo)')
        yield ('redo', ('Redo %s' % ractions[-1].name) if ractions else '(Redo)')
        yield ('open', 'Open document...')
