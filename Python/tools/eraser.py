from worldobj import EraserPointer
from model import ModelStep
import selection
from .base import BaseTool


class Eraser(BaseTool):

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position,
                        ignore=set([selection.find_closest_vertex]))
            self.app.flash(EraserPointer(closest.get_point()))
            closest.flash_flat(selection.DELETE_COLOR)

            if ctrl.trigger_pressed():
                self.action_delete(closest)
                return None

        return None

    def action_delete(self, closest):
        if isinstance(closest, selection.SelectAlongEdge):
            edges = [closest.edge]
            faces = [face for face in self.app.model.faces if closest.edge in face.edges]
        elif isinstance(closest, selection.SelectOnFace):
            edges = []
            faces = [closest.face]
        else:
            return

        text = []
        if edges:
            text.append("%d edge%s" % (len(edges), "s" * (len(edges) > 1)))
        if faces:
            text.append("%d face%s" % (len(faces), "s" * (len(faces) > 1)))

        step = ModelStep(self.app.model, "Erase %s" % (' + '.join(text),))
        for fe in edges + faces:
            step.remove(fe)
        self.app.execute_step(step)