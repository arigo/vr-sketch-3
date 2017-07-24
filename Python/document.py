import os
import json
from model import Edge, Face, Model, ModelStep
from util import Vector3

HEADER = "vrsketch"
VERSION = "0.1"


class VRSketchFile(object):

    def __init__(self, filename):
        self.filename = filename
        self.model = Model()
        self.undoable_actions = []
        self.redoable_actions = []
        if os.path.exists(filename):
            with self.openfile('rb') as f:
                self._load_data(f)
        else:
            with self.openfile('wb+') as f:
                write_header(f)
            self.populate_initial_model()

    def openfile(self, mode):
        return open(self.filename, mode)

    def _enum_json(self, f):
        f.seek(0)
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.endswith('\n'):
                raise ValueError("file contains a non-terminated line")
            line = line.strip()
            if line:
                yield (pos, json.loads(line))


    def _load_data(self, f):
        # assumes an empty 'self.model' and 'self.undoable_actions',
        # and fill them by loading the file
        enum = self._enum_json(f)
        _, header = next(enum)
        if header.get("a") != HEADER:
            raise ValueError(header.get("a"))
        #
        edges_by_eid = {}
        faces_by_fid = {}
        for pos, entry in enum:
            model_step = ModelStep(self.model, entry["a"])
            model_step.file_position = pos

            if "remove" in entry:
                for remove_id in entry["remove"]:
                    if remove_id.startswith('e'):
                        eid = int(remove_id[1:])
                        item = edges_by_eid[eid]
                    elif remove_id.startswith('f'):
                        fid = int(remove_id[1:])
                        item = faces_by_fid[fid]
                    else:
                        raise ValueError(remove_id)
                    model_step.fe_remove.add(item)

            if "add" in entry:
                for add1 in entry["add"]:
                    add_id = add1["id"]
                    if add_id.startswith('e'):
                        eid = int(add_id[1:])
                        v1 = Vector3(*add1["v1"])
                        v2 = Vector3(*add1["v2"])
                        item = Edge(v1, v2, eid=eid)
                        edges_by_eid[eid] = item
                    elif add_id.startswith('f'):
                        fid = int(add_id[1:])
                        edges = []
                        for edge_id in add1["edges"]:
                            assert edge_id.startswith('e')
                            eid = int(edge_id[1:])
                            edges.append(edges_by_eid[eid])
                        item = Face(edges, fid=fid)
                        faces_by_fid[fid] = item
                    else:
                        raise ValueError(add_id)
                    model_step.fe_add.append(item)

            model_step._apply_to_model()
            self.undoable_actions.append(model_step)


    def _record_undoable_action(self, model_step):
        with self.openfile('rb+') as f:
            f.seek(0, 2)
            model_step.file_position = f.tell()
            write_model_step(f, model_step)
        self.undoable_actions.append(model_step)


    def record_undoable_action(self, model_step):
        del self.redoable_actions[:]
        self._record_undoable_action(model_step)

    def undo_once(self, app):
        if self.undoable_actions:
            model_step = self.undoable_actions[-1]
            with self.openfile('rb+') as f:
                f.seek(model_step.file_position)
                model_step_rev = model_step.reversed()
                model_step_rev.apply(app)
                f.truncate()
            self.undoable_actions.pop()
            self.redoable_actions.append(model_step)

    def redo_once(self, app):
        if self.redoable_actions:
            model_step = self.redoable_actions[-1]
            model_step.apply(app)
            self.redoable_actions.pop()
            self._record_undoable_action(model_step)

    def populate_initial_model(self):
        v1 = Vector3(0, 0, 1)
        v2 = Vector3(1, 0, 1)
        v3 = Vector3(1, 1, 1)
        v4 = Vector3(0, 1, 1)
        step = ModelStep(self.model, "Initial rectangle")
        e1 = step.add_edge(v1, v2)
        e2 = step.add_edge(v2, v3)
        e3 = step.add_edge(v3, v4)
        e4 = step.add_edge(v4, v1)
        step.add_face([e1, e2, e3, e4])
        step._apply_to_model()
        self.record_undoable_action(step)


def _emit_json(f, entry):
    line = json.dumps(entry, sort_keys=True)
    assert '\n' not in line
    line += '\n'
    f.write(line)

def write_header(f):
    _emit_json(f, {"a": HEADER, "version": VERSION})
    f.write('\n')

def write_model_step(f, model_step):
    entry = {"a": model_step.name}

    if model_step.fe_remove:
        remove_ids = []
        for fe in model_step.fe_remove:
            if isinstance(fe, Edge):
                remove_ids.append("e%d" % fe.eid)
            elif isinstance(fe, Face):
                remove_ids.append("f%d" % fe.fid)
            else:
                raise TypeError(type(fe))
        entry["remove"] = remove_ids

    if model_step.fe_add:
        adds1 = []
        adds2 = []
        for fe in model_step.fe_add:
            if isinstance(fe, Edge):
                adds1.append({"id": "e%d" % fe.eid,
                              "v1": fe.v1.tolist(),
                              "v2": fe.v2.tolist()})
            elif isinstance(fe, Face):
                edges = ["e%d" % e.eid for e in fe.edges]
                adds2.append({"id": "f%d" % fe.fid,
                              "edges": edges})
            else:
                raise TypeError(type(fe))
        entry["add"] = adds1 + adds2

    _emit_json(f, entry)
