import worldobj

PRESS_TRIGGER = 1
PRESS_GRIP    = 2


class Controller(object):

    def __init__(self, app):
        self.app = app

    def update(self, pos, pressed):
        self.pos = pos
        self.pressed = pressed
        #self.flash(worldobj.Cylinder(cpos, Vector3(0, 0, 0), color=0x00FF00))

    def update_together(self, other):
        if self.pressed & other.pressed & PRESS_GRIP:
            self.app.flash(worldobj.Cylinder(
                    self.pos, other.pos, color=0x202020))
