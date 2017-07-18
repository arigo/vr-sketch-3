from worldobj import SelectPointer
from model import ModelStep
import selection
from .base import BaseTool


class Select(BaseTool):
    KEEP_SELECTION = True

    def handle_hover(self, controllers):
        for ctrl in controllers:
            if ctrl.is_trigger_down() and not ctrl.trigger_pressed():
                continue

            closest = selection.find_closest(self.app, ctrl.position,
                        ignore=set([selection.find_closest_vertex]))
            edges = closest.individual_edges()
            edges_add = any(set(edges) - self.app.selected_edges)
            if edges:
                if edges_add:
                    color = selection.ADD_COLOR
                else:
                    color = selection.SELECTED_COLOR
                closest.flash_flat(color)
            self.app.flash(SelectPointer(closest.get_point()))

            if edges and ctrl.trigger_pressed():
                if edges_add:
                    self.action_add(edges)
                else:
                    self.action_remove(edges)
                return None

        return None

    def action_add(self, edges):
        self.app.selected_edges.update(edges)
        self.app.selection_updated()

    def action_remove(self, edges):
        self.app.selected_edges.difference_update(edges)
        self.app.selection_updated()