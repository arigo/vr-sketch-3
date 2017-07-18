import weakref
import util, model, controller, worldobj
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
        self.model2worldobj = {}
        self.ctrlmgr = controller.ControllersMgr(self)
        self.undoable_actions = []
        self.redoable_actions = []
        self.manual_tokens = weakref.WeakKeyDictionary()
        self.next_manual_token = 1

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

    def _add_edge_or_face(self, edge_or_face):
        if isinstance(edge_or_face, model.Edge):
            wo = worldobj.Stem(edge_or_face.v1, edge_or_face.v2, 0x101010)   # very dark
        elif isinstance(edge_or_face, model.Face):
            wo = worldobj.Polygon([edge.v1 for edge in edge_or_face.edges])
        else:
            raise AssertionError(repr(edge_or_face))
        self.model2worldobj[edge_or_face] = wo
        self.display(wo)

    def _remove_edge_or_face(self, edge_or_face):
        wo = self.model2worldobj.pop(edge_or_face)
        self.destroy(wo)

    def execute_step(self, model_step):
        model_step.consolidate(self)
        model_step.apply(self)
        self.record_undoable_action(model_step.reversed())

    def execute_temporary_step(self, model_step):
        model_step.consolidate_temporary()
        model_step.apply(self)

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
            getattr(self, '_handle_click_' + id)()


    def record_undoable_action(self, undoable_action):
        del self.redoable_actions[:]
        self.undoable_actions.append(undoable_action)

    def _handle_click_undo(self):
        if self.undoable_actions:
            self.undoable_actions[-1].apply(self)
            action = self.undoable_actions.pop()
            self.redoable_actions.append(action.reversed())

    def _handle_click_redo(self):
        if self.redoable_actions:
            self.redoable_actions[-1].apply(self)
            action = self.redoable_actions.pop()
            self.undoable_actions.append(action.reversed())


    def fetch_manual_token(self, owner, key):
        try:
            d = self.manual_tokens[owner]
        except KeyError:
            d = self.manual_tokens[owner] = {}
        try:
            result = d[key]
        except KeyError:
            result = d[key] = self.next_manual_token
            self.next_manual_token += 1
        return result

    def handle_manual_enter(self, token, new_value):
        for owner, d in self.manual_tokens.items():
            for key, value in d.items():
                if value == token:
                    owner.manual_enter(key, new_value)
                    return


def initialize_functions(ffi, _fn_update, _fn_approx_plane, _fn_show_menu):
    global fn_update
    fn_update = _fn_update

    def _approx_plane(coords):
        result = ffi.new("float[4]")
        _fn_approx_plane(coords, len(coords), result)
        return result
    util._approx_plane = _approx_plane

    controller._show_menu = _fn_show_menu
