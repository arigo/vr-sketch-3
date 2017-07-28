from worldobj import SelectPointer, SelectPointerPlus, SelectPointerMinus, Stem
from util import Vector3
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
            edges = set(edges)
            for e in list(edges):
                for e1 in self.app.model.edges:
                    if e1.v1 == e.v2 and e1.v2 == e.v1:
                        edges.add(e1)

            edges_add = any(edges - self.app.selected_edges)
            cls = SelectPointer
            if edges:
                if edges_add:
                    cls = SelectPointerPlus
                    color = selection.ADD_COLOR
                else:
                    cls = SelectPointerMinus
                    color = selection.SELECTED_COLOR
                closest.flash_flat(color)
            self.app.flash(cls(closest.get_point()))

            if ctrl.trigger_pressed():
                if edges:
                    if edges_add:
                        self.action_add(edges)
                    else:
                        self.action_remove(edges)
                    return None
                else:
                    return self.start_box_select(ctrl)

        return None

    def action_add(self, edges):
        self.app.selected_edges.update(edges)
        self.app.selection_updated()

    def action_remove(self, edges):
        self.app.selected_edges.difference_update(edges)
        self.app.selection_updated()

    def start_box_select(self, ctrl):
        self.source_position = ctrl.position
        return ctrl

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        source = self.source_position
        target = follow_ctrl.position

        def show_edge(src, coord_name, newvalue):
            self.app.flash(Stem(src, src.withcoord(coord_name, newvalue), 0xC040FF))

        show_edge(source, 'x', target.x)
        show_edge(source.withcoord('y', target.y), 'x', target.x)
        show_edge(source.withcoord('z', target.z), 'x', target.x)
        show_edge(source.withcoord('y', target.y).withcoord('z', target.z), 'x', target.x)
        show_edge(source, 'y', target.y)
        show_edge(source.withcoord('x', target.x), 'y', target.y)
        show_edge(source.withcoord('z', target.z), 'y', target.y)
        show_edge(source.withcoord('x', target.x).withcoord('z', target.z), 'y', target.y)
        show_edge(source, 'z', target.z)
        show_edge(source.withcoord('x', target.x), 'z', target.z)
        show_edge(source.withcoord('y', target.y), 'z', target.z)
        show_edge(source.withcoord('x', target.x).withcoord('y', target.y), 'z', target.z)

        x1 = min(source.x, target.x)
        x2 = max(source.x, target.x)
        y1 = min(source.y, target.y)
        y2 = max(source.y, target.y)
        z1 = min(source.z, target.z)
        z2 = max(source.z, target.z)

        def in_box(v):
            return (x1 <= v.x <= x2 and
                    y1 <= v.y <= y2 and
                    z1 <= v.z <= z2)

        self.app.selected_edges.clear()
        for edge in self.app.model.edges:
            if in_box(edge.v1) and in_box(edge.v2):
                self.app.selected_edges.add(edge)
        self.app.selection_updated()
