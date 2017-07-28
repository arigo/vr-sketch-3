from worldobj import EraserPointer
from model import ModelStep
import selection
from .base import BaseTool


class Eraser(BaseTool):
    KEEP_SELECTION = True

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position,
                        ignore=set([selection.find_closest_vertex]))
            self.app.flash(EraserPointer(closest.get_point(), ctrl))

            edges = set()
            faces = set()
            all_selected = False
            if isinstance(closest, selection.SelectAlongEdge):
                all_selected = closest.edge in self.app.selected_edges
                edges.add(closest.edge)
            elif isinstance(closest, selection.SelectOnFace):
                all_selected = all(edge in self.app.selected_edges for edge in closest.face.edges)
                faces.add(closest.face)
                closest.flash_flat(selection.DELETE_COLOR)
            if all_selected:
                edges.update(self.app.selected_edges)

            for edge in edges:
                selection.SelectAlongEdge(self.app, edge, 0.5).flash_flat(selection.DELETE_COLOR)

            if ctrl.trigger_pressed():
                self.action_delete(edges, faces)
                return None

        return None

    def action_delete(self, edges, faces):
        text = []
        if edges:
            text.append("-%d edge%s" % (len(edges), "s" * (len(edges) > 1)))

        for edge in list(edges):
            for e1 in self.app.model.edges:
                if ((edge.v1 == e1.v1 and edge.v2 == e1.v2) or
                    (edge.v1 == e1.v2 and edge.v2 == e1.v1)):
                    edges.add(e1)
        for edge in edges:
            for face in self.app.model.faces:
                if edge in face.edges:
                    faces.add(face)

        if faces:
            text.append("-%d face%s" % (len(faces), "s" * (len(faces) > 1)))
        if len(text) == 0:
            return

        step = ModelStep(self.app.model, ', '.join(text))
        for fe in faces:
            step.remove(fe)
        for fe in edges:
            step.remove(fe)
        self.app.execute_step(step)
