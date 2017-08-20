import os
import cffi
import model
from util import Vector3


DIR = os.path.dirname(os.path.abspath(__file__))

SCALE = 0.0254     # inches inside .skp files...


ffi = cffi.FFI()
ffi.cdef("""
    enum SUResult {
      SU_ERROR_NONE = 0,
      SU_ERROR_NULL_POINTER_INPUT,
      SU_ERROR_INVALID_INPUT,
      SU_ERROR_NULL_POINTER_OUTPUT,
      SU_ERROR_INVALID_OUTPUT,
      SU_ERROR_OVERWRITE_VALID,
      SU_ERROR_GENERIC,
      SU_ERROR_SERIALIZATION,
      SU_ERROR_OUT_OF_RANGE,
      SU_ERROR_NO_DATA,
      SU_ERROR_INSUFFICIENT_SIZE,
      SU_ERROR_UNKNOWN_EXCEPTION,
      SU_ERROR_MODEL_INVALID,
      SU_ERROR_MODEL_VERSION,
      SU_ERROR_LAYER_LOCKED,
      SU_ERROR_DUPLICATE,
      SU_ERROR_PARTIAL_SUCCESS,
      SU_ERROR_UNSUPPORTED,
      SU_ERROR_INVALID_ARGUMENT
    };
    typedef enum SUResult SU_RESULT;
    typedef struct _SUModel *SUModelRef;
    typedef struct _SUEntities *SUEntitiesRef;
    typedef struct _SUFace *SUFaceRef;
    typedef struct _SULoop *SULoopRef;
    typedef struct _SUVertex *SUVertexRef;
    typedef struct _SUMaterial *SUMaterialRef;
    typedef struct _SUGroup *SUGroupRef;
    typedef unsigned char SUByte;

    struct SUPoint3D {
        double x, y, z;
    };

    typedef struct {
        SUByte red;
        SUByte green;
        SUByte blue;
        SUByte alpha;
    } SUColor;

    struct SUTransformation {
        double values[16];
    };

    void SUInitialize();
    SU_RESULT SUModelCreateFromFile(SUModelRef *model, const char *file_path);
    SU_RESULT SUModelGetEntities(SUModelRef model, SUEntitiesRef *entities);
    SU_RESULT SUEntitiesGetNumFaces(SUEntitiesRef entities, size_t *count);
    SU_RESULT SUEntitiesGetFaces(SUEntitiesRef entities, size_t len,
                                 SUFaceRef faces[], size_t *count);
    SU_RESULT SUFaceGetOuterLoop(SUFaceRef face, SULoopRef *loop);
    SU_RESULT SULoopGetNumVertices(SULoopRef loop, size_t *count);
    SU_RESULT SULoopGetVertices(SULoopRef loop, size_t len,
                                SUVertexRef vertices[], size_t *count);
    SU_RESULT SUVertexGetPosition(SUVertexRef vertex,
                                  struct SUPoint3D *position);

    SU_RESULT SUFaceGetFrontMaterial(SUFaceRef face, SUMaterialRef *material);
    SU_RESULT SUFaceGetBackMaterial(SUFaceRef face, SUMaterialRef *material);
    SU_RESULT SUMaterialGetColor(SUMaterialRef material, SUColor *color);

    SU_RESULT SUGroupGetTransform(SUGroupRef group, struct SUTransformation *transform);
    SU_RESULT SUEntitiesGetNumGroups(SUEntitiesRef entities, size_t *count);
    SU_RESULT SUEntitiesGetGroups(SUEntitiesRef entities, size_t len,
                                  SUGroupRef groups[], size_t *count);
    SU_RESULT SUGroupGetEntities(SUGroupRef group, SUEntitiesRef *entities);
""")

lib = ffi.dlopen(os.path.join(DIR, 'SketchUpAPI.dll'))
lib.SUInitialize()


def err(code):
    if code != 0:
        text = ffi.string(ffi.cast("SU_RESULT", code))
        raise ValueError(text)

def get_face_color(face, meth):
    matref_p = ffi.new("SUMaterialRef[1]")
    if getattr(lib, meth)(face, matref_p) != 0:
        return None
    matref = matref_p[0]
    color_p = ffi.new("SUColor[1]")
    if lib.SUMaterialGetColor(matref, color_p) != 0:
        return None
    return (color_p[0].red << 16 |
            color_p[0].green << 8 |
            color_p[0].blue)


class STransform:
    def __init__(self, values):
        self.values = list(values)
        assert len(self.values) == 16
    
    def apply(self, vec3):
        v = Vector3(
            self.values[0] * vec3.x + self.values[4] * vec3.y + self.values[8] * vec3.z + self.values[12],
            self.values[1] * vec3.x + self.values[5] * vec3.y + self.values[9] * vec3.z + self.values[13],
            self.values[2] * vec3.x + self.values[6] * vec3.y + self.values[10]* vec3.z + self.values[14])
        w = self.values[3] * vec3.x + self.values[7] * vec3.y + self.values[11]* vec3.z + self.values[15]
        return v / w

IDENTITY = STransform([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

class SFace:
    def __init__(self, v_list, color):
        self.v_list = v_list
        self.color = color

    def emit(self, step, model_group):
        v_list = self.v_list
        edges = [step.add_edge(model_group, v_list[j - 1], v_list[j])
                    for j in range(len(v_list))]
        face = step.add_face(edges)
        face.physics = model.Physics(color=self.color)

class SGroup:
    def __init__(self, group_matrix, sfaces, sgroups):
        self.group_matrix = group_matrix
        self.sfaces = sfaces
        self.sgroups = sgroups

    def _all_sfaces(self):
        for sface in self.sfaces:
            yield sface
        for sgroup in self.sgroups:
            for sface in sgroup._all_sfaces():
                yield sface

    def apply_transform(self):
        for sgroup in self.sgroups:
            sgroup.apply_transform()
        matrix = self.group_matrix
        for sface in self._all_sfaces():
            sface.v_list = [matrix.apply(v) for v in sface.v_list]

    def enum_vertices(self):
        for sface in self.sfaces:
            for v in sface.v_list:
                yield v
        for sgroup in self.sgroups:
            for v in sgroup.enum_vertices():
                yield v

    def print_bounds(self, indent=""):
        if self.sfaces:
            minx = miny = minz = 1e99
            maxx = maxy = maxz = -1e99
            for sface in self.sfaces:
                for v in sface.v_list:
                    if v.x < minx: minx = v.x
                    if v.y < miny: miny = v.y
                    if v.z < minz: minz = v.z
                    if v.x > maxx: maxx = v.x
                    if v.y > maxy: maxy = v.y
                    if v.z > maxz: maxz = v.z
            print ('%sBounds: %f, %f, %f\n'
                   '%s     -> %f, %f, %f') % (indent, minx, miny, minz, indent, maxx, maxy, maxz)
        for sgroup in self.sgroups:
            sgroup.print_bounds(indent + "  ")

    def emit(self, step, model_group):
        print "Emitting group with %d faces" % (len(self.sfaces),)
        for sface in self.sfaces:
            sface.emit(step, model_group)
        for sgroup in self.sgroups:
            subgroup = model.Group(model_group)
            sgroup.emit(step, subgroup)


def _load_entities(entitiesref):
    # --- load faces ---
    count_p = ffi.new("size_t[1]")
    err(lib.SUEntitiesGetNumFaces(entitiesref, count_p))
    numfaces = count_p[0]

    faces = ffi.new("SUFaceRef[]", numfaces)

    retrieved_p = ffi.new("size_t[1]")
    err(lib.SUEntitiesGetFaces(entitiesref, numfaces, faces, retrieved_p))
    retrieved = retrieved_p[0]

    position_p = ffi.new("struct SUPoint3D *")

    sfaces = []

    for i in range(retrieved):
        loopref_p = ffi.new("SULoopRef[1]")
        err(lib.SUFaceGetOuterLoop(faces[i], loopref_p))
        loopref = loopref_p[0]

        err(lib.SULoopGetNumVertices(loopref, count_p))
        vertexcount = count_p[0]
        if vertexcount <= 0:
            continue        # ignore

        vertices = ffi.new("SUVertexRef[]", vertexcount)

        err(lib.SULoopGetVertices(loopref, vertexcount, vertices,
                                  retrieved_p))
        vertex_retrieved = retrieved_p[0]

        v_list = []
        for j in range(vertex_retrieved):
            err(lib.SUVertexGetPosition(vertices[j], position_p))
            v_list.append(Vector3(position_p.x, position_p.y, position_p.z))

        # XXX this misses the edges that are not attached to faces

        color = get_face_color(faces[i], "SUFaceGetFrontMaterial")
        if color is None:
            color = get_face_color(faces[i], "SUFaceGetBackMaterial")
        sfaces.append(SFace(v_list, color))

    # --- load groups ---
    err(lib.SUEntitiesGetNumGroups(entitiesref, count_p))
    numgroups = count_p[0]

    groups = ffi.new("SUGroupRef[]", numgroups)
    err(lib.SUEntitiesGetGroups(entitiesref, numgroups, groups, retrieved_p))
    retrieved = retrieved_p[0]

    sgroups = []

    for i in range(retrieved):
        transform_p = ffi.new("struct SUTransformation[1]")
        err(lib.SUGroupGetTransform(groups[i], transform_p))
        matrix = STransform(transform_p[0].values)

        entitiesref_p = ffi.new("SUEntitiesRef[1]")
        err(lib.SUGroupGetEntities(groups[i], entitiesref_p))
        ssfaces, ssgroups = _load_entities(entitiesref_p[0])
        sgroups.append(SGroup(matrix, ssfaces, ssgroups))

    return sfaces, sgroups


def load(filename):
    modelref_p = ffi.new("SUModelRef[1]")
    err(lib.SUModelCreateFromFile(modelref_p, filename))
    modelref = modelref_p[0]

    entitiesref_p = ffi.new("SUEntitiesRef[1]")
    err(lib.SUModelGetEntities(modelref, entitiesref_p))
    sfaces, sgroups = _load_entities(entitiesref_p[0])
    sroot = SGroup(IDENTITY, sfaces, sgroups)
    sroot.apply_transform()
    #sroot.print_bounds()
    #import pdb;pdb.set_trace()

    # recenter the model so that all coordinates start at (0, 0, 0) and grow positive from there
    minx = miny = minz = 1e99
    for v in sroot.enum_vertices():
        if v.x < minx: minx = v.x
        if v.y < miny: miny = v.y
        if v.z < minz: minz = v.z
    for v in sroot.enum_vertices():
        v.x -= minx
        v.y -= miny
        v.z -= minz
        v.x *= SCALE
        v.y *= SCALE
        v.z *= SCALE

    step = model.ModelStep(model.Model(), "Loaded from .skp")
    sroot.emit(step, step.model.root_group)
    step._apply_to_model()
    return step.model


def save(model, filename):
    raise NotImplementedError
