import setuptools
import cffi

ffibuilder = cffi.FFI()

ffibuilder.embedding_api("""
    int pyunityvr_init(void (*__stdcall signal_error)(wchar_t *),
                       void (*__stdcall update)(int, int, float[], int),
                       void (*__stdcall approx_plane)(float[], int, float[]));
    int pyunityvr_frame(int num_controllers, float controllers[]);
""")

ffibuilder.set_source("PyUnityVR_cffi", "")

ffibuilder.embedding_init_code(r"""
import sys
sys.path.insert(0, 'Python')
import PyUnityVR.ffi_interface
""")

ffibuilder.compile(target="PyUnityVR_cffi.*", verbose=True)
