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

    struct SUPoint3D {
        double x, y, z;
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
""")

lib = ffi.dlopen(os.path.join(DIR, 'SketchUpAPI.dll'))
lib.SUInitialize()


def err(code):
    if code != 0:
        text = ffi.string(ffi.cast("SU_RESULT", code))
        raise ValueError(text)


def load(filename):
    step = model.ModelStep(model.Model(), "Loaded from .skp")

    modelref_p = ffi.new("SUModelRef[1]")
    err(lib.SUModelCreateFromFile(modelref_p, filename))
    modelref = modelref_p[0]

    entitiesref_p = ffi.new("SUEntitiesRef[1]")
    err(lib.SUModelGetEntities(modelref, entitiesref_p))
    entitiesref = entitiesref_p[0]

    count_p = ffi.new("size_t[1]")
    err(lib.SUEntitiesGetNumFaces(entitiesref, count_p))
    numfaces = count_p[0]

    faces = ffi.new("SUFaceRef[]", numfaces)

    retrieved_p = ffi.new("size_t[1]")
    err(lib.SUEntitiesGetFaces(entitiesref, numfaces, faces, retrieved_p))
    retrieved = retrieved_p[0]

    position_p = ffi.new("struct SUPoint3D *")

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
            v_list.append(Vector3(position_p.x, position_p.y, position_p.z) * SCALE)

        edges = [step.add_edge(v_list[j - 1], v_list[j])
                 for j in range(len(v_list))]
        step.add_face(edges)
        # XXX this misses the edges that are not attached to faces

    step._apply_to_model()
    return step.model


def save(model, filename):
    raise NotImplementedError
