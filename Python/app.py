from PyUnityVR_cffi import ffi
from util import Vector3

KIND_DESTROYED = 0


class WorldObject(object):
    _index = None


class App(object):

    def __init__(self, fn_update):
        self.fn_update = fn_update
        self.freelists = {}
        self.pending_removes = {}
        self.pending_updates = set()
        self.destroy_later = []
        self.num_world_objs = 0
        self.controllers = []

    def display(self, worldobj):
        self.pending_updates.add(worldobj)

    def flash(self, worldobj):
        self.pending_updates.add(worldobj)
        self.destroy_later.append(worldobj)

    def destroy(self, worldobj):
        kind = worldobj._kind
        if kind != KIND_DESTROYED:
            worldobj._kind = KIND_DESTROYED
            index = worldobj._index
            if index is not None:
                worldobj._index = None
                self.pending_removes.setdefault(kind, []).append(index)

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
        self.fn_update(index, kind, raw, len(raw))

    def handle_frame(self, num_controllers, controllers):
        if len(self.controllers) != num_controllers:
            from controller import Controller

            while len(self.controllers) > num_controllers:
                self.controllers.pop()
            while len(self.controllers) < num_controllers:
                self.controllers.append(Controller(self))

        for i in range(num_controllers):
            cpos = Vector3(controllers[i * 4],
                           controllers[i * 4 + 1],
                           controllers[i * 4 + 2])
            pressed = int(controllers[i * 4 + 3])
            self.controllers[i].update(cpos, pressed)

        if num_controllers == 2:
            self.controllers[0].update_together(self.controllers[1])

        # send updates... first all new or modified objects,
        # possibly reusing some indexes that are to be freed
        for go in self.pending_updates:
            self._really_update(go)
        self.pending_updates.clear()

        # then, we really free the indexes that are still marked as such
        for freelist in self.pending_removes.values():
            for index in freelist:
                self.fn_update(index, KIND_DESTROYED, [], 0)
        self.pending_removes.clear()

        # finally, we move 'destroy_later' to 'pending_removes' for
        # the next frame
        for go in self.destroy_later:
            self.destroy(go)
        del self.destroy_later[:]
