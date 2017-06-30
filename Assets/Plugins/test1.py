import setuptools
import cffi

ffibuilder = cffi.FFI()

ffibuilder.embedding_api("""
    int pyunityvr_init(void (*__stdcall signal_error)(wchar_t *),
                       void (*__stdcall update)(int, int, float[], int),
                       void (*__stdcall approx_plane)(float[], int, float[]),
                       void (*__stdcall show_menu)(int, wchar_t *));
    int pyunityvr_frame(int num_controllers, float controllers[]);
    int pyunityvr_click(wchar_t *id);
    int pyunityvr_manual_enter(int token, float value);
""")

ffibuilder.set_source("PyUnityVR_cffi", "")

ffibuilder.embedding_init_code(r"""
import sys
sys.path.insert(0, 'Python')
import PyUnityVR.ffi_interface
""")

ffibuilder.compile(target="PyUnityVR_cffi.*", verbose=True)
