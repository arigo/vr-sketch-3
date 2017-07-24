import os
import cffi

DIR = os.path.dirname(os.path.abspath(__file__))

ffi = cffi.FFI()
ffi.cdef("""
    enum SUResult {
   12   SU_ERROR_NONE = 0, 
   13 
   14   SU_ERROR_NULL_POINTER_INPUT, 
   15 
   16   SU_ERROR_INVALID_INPUT, 
   17 
   18 
   19   SU_ERROR_NULL_POINTER_OUTPUT, 
   20 
   21   SU_ERROR_INVALID_OUTPUT, 
   22 
   23 
   24   SU_ERROR_OVERWRITE_VALID, 
   25 
   26 
   27 
   28   SU_ERROR_GENERIC, 
   29 
   30   SU_ERROR_SERIALIZATION, 
   31 
   32 
   33   SU_ERROR_OUT_OF_RANGE, 
   34 
   35 
   36   SU_ERROR_NO_DATA, 
   37 
   38 
   39 
   40   SU_ERROR_INSUFFICIENT_SIZE, 
   41 
   42 
   43   SU_ERROR_UNKNOWN_EXCEPTION, 
   44 
   45   SU_ERROR_MODEL_INVALID, 
   46 
   47   SU_ERROR_MODEL_VERSION, 
   48 
   49 
   50   SU_ERROR_LAYER_LOCKED, 
   51 
   52   SU_ERROR_DUPLICATE,   
   53 
   54   SU_ERROR_PARTIAL_SUCCESS,  
   55 
   56 
   57 
   58   SU_ERROR_UNSUPPORTED, 
   59 
   60   SU_ERROR_INVALID_ARGUMENT 
   61 };

    void SUInitialize();
    SU_RESULT SUModelCreateFromFile(SUModelRef *model, const char *file_path);
""")

lib = ffi.dlopen(os.path.join(DIR, 'SketchUpAPI.dll'))
lib.SUInitialize()


