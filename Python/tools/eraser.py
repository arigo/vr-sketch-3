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
            self.app.flash(EraserPointer(closest.get_point()))

            closests = [closest]
            if isinstance(closest, selection.SelectAlongEdge):
                if closest.edge in self.app.selected_edges:
                    closests = [selection.SelectAlongEdge(self.app, edge, 0.5) for edge in self.app.selected_edges]

            for closest in closests:
                closest.flash_flat(selection.DELETE_COLOR)

            if ctrl.trigger_pressed():
                self.action_delete(closests)
                return None

        return None

    def action_delete(self, closests):
        edges = set()
        faces = set()
        for closest in closests:
            if isinstance(closest, selection.SelectAlongEdge):
                edges.add(closest.edge)
                for face in self.app.model.faces:
                    if closest.edge in face.edges:
                        faces.add(face)
            elif isinstance(closest, selection.SelectOnFace):
                faces.add(closest.face)

        edges = list(edges)
        faces = list(faces)
        text = []
        if edges:
            text.append("-%d edge%s" % (len(edges), "s" * (len(edges) > 1)))
        if faces:
            text.append("-%d face%s" % (len(faces), "s" * (len(faces) > 1)))
        if len(text) == 0:
            return

        step = ModelStep(self.app.model, ', '.join(text))
        for fe in edges + faces:
            step.remove(fe)
        self.app.execute_step(step)