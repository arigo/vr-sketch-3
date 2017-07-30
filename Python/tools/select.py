from worldobj import SelectPointer, SelectPointerPlus, SelectPointerMinus, Stem
from util import Vector3
from model import ModelStep, Group
import selection
from .base import BaseTool


class Select(BaseTool):
    KEEP_SELECTION = True

    def handle_hover(self, controllers):
        for ctrl in controllers:
            if ctrl.is_trigger_down() and not ctrl.trigger_pressed():
                continue

            closest = selection.find_closest(self.app, ctrl.position,
                        ignore=set([selection.find_closest_vertex]),
                        only_group=self.app.curgroup)
            operation = 0
            if isinstance(closest, selection.SelectVoid):
                closest = selection.find_subgroup(self.app, ctrl.position)
                if isinstance(closest, selection.SelectGroup):
                    operation = -1 if closest.group in self.app.selected_subgroups else 1
                    op_arg = closest.group
            else:
                edges = closest.individual_edges()
                edges = set(edges)
                for e in list(edges):
                    for e1 in self.app.getcuredges():
                        if e1.v1 == e.v2 and e1.v2 == e.v1:
                            edges.add(e1)
                if edges:
                    operation = 1 if any(edges - self.app.selected_edges) else -1
                    op_arg = edges

            cls = SelectPointer
            if operation != 0:
                if operation == 1:
                    cls = SelectPointerPlus
                    color = selection.ADD_COLOR
                else:
                    cls = SelectPointerMinus
                    color = selection.SELECTED_COLOR
                closest.flash_flat(color)
            self.app.flash(cls(closest.get_point(), ctrl))

            if ctrl.trigger_pressed():
                if operation != 0:
                    self.action(operation, op_arg)
                    return None
                else:
                    return self.start_box_select(ctrl)

        return None

    def action(self, operation, op_arg):
        if isinstance(op_arg, Group):
            if operation == 1:
                self.app.selected_subgroups.add(op_arg)
            else:
                self.app.selected_subgroups.remove(op_arg)
            also_faces = True
        else:
            if operation == 1:
                self.app.selected_edges.update(op_arg)
            else:
                self.app.selected_edges.difference_update(op_arg)
            also_faces = False
        self.app.selection_updated(also_faces=also_faces)

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
        self.app.selected_subgroups.clear()
        for edge in self.app.getcuredges():
            if in_box(edge.v1) and in_box(edge.v2):
                self.app.selected_edges.add(edge)
        self.app.selection_updated(also_faces=True)
