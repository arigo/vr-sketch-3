import controller
from .base import BaseTool


class Teleport(BaseTool):

    def __init__(self, app):
        BaseTool.__init__(self, app)
        controller._show_menu(2000, u"")    # enable teleporter

    def unselect_now(self):
        controller._show_menu(2001, u"")    # disable teleporter

    def handle_controllers(self, controllers):
        pass