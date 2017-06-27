from PyUnityVR_cffi import ffi
import util, model, controller
from util import Vector3


KIND_DESTROYED = 0


class App(object):

    def __init__(self):
        self.freelists = {}
        self.pending_removes = {}
        self.pending_updates_seen = set()
        self.pending_updates = []
        self.destroy_later = []
        self.num_world_objs = 0
        self.model = model.Model()
        self.ctrlmgr = controller.ControllersMgr(self)

    def display(self, worldobj):
        if worldobj not in self.pending_updates_seen:
            self.pending_updates_seen.add(worldobj)
            self.pending_updates.append(worldobj)

    def flash(self, worldobj):
        self.display(worldobj)
        self.destroy_later.append(worldobj)

    def destroy(self, worldobj):
        kind = worldobj._kind
        if kind != KIND_DESTROYED:
            worldobj._kind = KIND_DESTROYED
            index = worldobj._index
            if index is not None:
                worldobj._index = None
                self.pending_removes.setdefault(kind, []).append(index)

    def add_edge(self, edge):
        self.model.edges.append(edge)
        self.display(edge)

    def add_face(self, face):
        self.model.faces.append(face)
        self.display(face)

    def scale_ctrl(self, distance):
        return distance / self.model_scale

    def _really_update(self, worldobj):
        kind = worldobj._kind
        if kind == KIND_DESTROYED:
            return
        index = worldobj._index
        if index is None:
            freelist = self.pending_removes.get(kind)
            if freelist:
                index = freelist.pop()
            else:
                index = self.num_world_objs
                self.num_world_objs += 1
            worldobj._index = index
        raw = worldobj.getrawdata()
        fn_update(index, kind, raw, len(raw))

    def handle_frame(self, num_controllers, controllers):
        self.ctrlmgr.handle_controllers(num_controllers, controllers)

        # send updates... first all new or modified objects,
        # possibly reusing some indexes that are to be freed
        for go in self.pending_updates:
            self._really_update(go)
        self.pending_updates_seen.clear()
        del self.pending_updates[:]

        # then, we really free the indexes that are still marked as such
        for freelist in self.pending_removes.values():
            for index in freelist:
                fn_update(index, KIND_DESTROYED, [], 0)
        self.pending_removes.clear()

        # finally, we move 'destroy_later' to 'pending_removes' for
        # the next frame
        for go in reversed(self.destroy_later):
            self.destroy(go)
        del self.destroy_later[:]

    def handle_click(self, id):
        if id.startswith("tool_"):
            self.ctrlmgr.load_tool(id[5:])
        else:
            raise ValueError(id)


def initialize_functions(ffi, _fn_update, _fn_approx_plane, _fn_show_menu):
    global fn_update
    fn_update = _fn_update

    def _approx_plane(coords):
        result = ffi.new("float[4]")
        _fn_approx_plane(coords, len(coords), result)
        return result
    util._approx_plane = _approx_plane

    controller._show_menu = _fn_show_menu