from worldobj import PushPullPointer, DashedStem, CrossPointer
from model import ModelStep
from util import Line, WholeSpace, Plane
import selection
from .base import BaseTool


class Pushpull(BaseTool):

    def handle_hover(self, controllers):
        for ctrl in controllers:
            closest = selection.find_closest(self.app, ctrl.position,
                        ignore=(selection.find_closest_vertex, selection.find_closest_edge))
            self.app.flash(PushPullPointer(closest.get_point()))
            closest.flash_flat(selection.ADD_COLOR)

            if ctrl.trigger_pressed() and isinstance(closest, selection.SelectOnFace):
                return self.start_push_pull(ctrl, closest)

        return None

    def handle_cancel(self):
        self.model_step.reversed().apply(self.app)

    def handle_accept(self):
        self.handle_cancel()
        self.app.execute_step(self.model_step)
        del self.model_step

    def handle_drag(self, follow_ctrl, other_ctrl=None):
        self.handle_cancel()

        subspace = WholeSpace()
        make_flashes = []
        p1 = self.source_position
        p2 = follow_ctrl.position

        # First, try to guide orthogonally from the source_face
        orthogonal_guide = Line(p1, self.source_face.plane.normal)
        _, d = orthogonal_guide.selection_distance(self.app, p2)
        if d <= 1.0:
            subspace = orthogonal_guide
            for edge in self.source_face.edges:
                make_flashes.append(lambda v1=edge.v1:
                                    DashedStem(v1, v1 + delta, 0xE6FFE6))

        # If the other controller is over a point position, guide orthgonally.
        # If it is over a plane, guide to that plane.  If it is over an edge,
        # guide to that line.
        if other_ctrl is not None:
            closest2 = selection.find_closest(self.app, other_ctrl.position)
            self.app.flash(CrossPointer(closest2.get_point()))
            ortho = False
            subspace1 = None
            if isinstance(closest2, selection.SelectOnFace):
                subspace1 = closest2.get_subspace()
            elif isinstance(closest2, selection.SelectAlongEdge):
                if closest2.fraction == 0.5:
                    ortho = True
                else:
                    subspace1 = closest2.get_subspace()
            elif isinstance(closest2, selection.SelectVertex):
                ortho = True

            if ortho:
                subspace1 = Plane.from_point_and_normal(closest2.get_point(), self.source_face.plane.normal)
            if subspace1 is not None:
                try:
                    subspace = subspace.intersect(subspace1)
                except EmptyIntersection:
                    pass
                else:
                    make_flashes.append(lambda v1=closest2.get_point(): DashedStem(v1, p2, 0xB8B8B8))

        p2 = subspace.project_point_inside(p2)
        delta = p2 - p1
        new_vertices = [e.v1 + delta for e in self.source_face.edges]

        for mf in make_flashes:
            self.app.flash(mf())

        self.model_step = ModelStep(self.app.model, "Push/Pull")
        new_edges = [self.model_step.add_edge(new_vertices[i + 1], new_vertices[i])
                     for i in range(-len(new_vertices), 0)]
        self.model_step.add_face(new_edges[::-1])
        
        for edge1, edge2 in zip(self.source_face.edges, new_edges):
            self.model_step.add_face([edge1,
                                      self.model_step.add_edge(edge1.v2, edge2.v1),
                                      edge2,
                                      self.model_step.add_edge(edge2.v2, edge1.v1)])

        self.app.execute_temporary_step(self.model_step)

    def start_push_pull(self, ctrl, closest):
        self.source_position = closest.get_point()
        self.source_face = closest.face
        self.model_step = ModelStep(self.app.model, "No movement")
        return ctrl