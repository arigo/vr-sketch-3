from PyUnityVR_cffi import ffi


_init_called = False
_error_callback = None

def signal_error(etype, value, tb):
    import os, sys
    import traceback
    #traceback.print_exception(etype, value, tb)
    # report by repeating the exception itself on the first two lines.
    # Unity displays the first two lines in the console, until we
    # click on it and then we see the full traceback.
    lines = []
    entries = traceback.extract_tb(tb)
    if entries:
        (filename, line_number, function_name, text) = entries[-1]
        filename = os.path.splitext(os.path.basename(filename))[0]
        lines.append('%s:%s in %s(): %s\n' % (
            filename, line_number, function_name, text))
    lines += traceback.format_exception_only(etype, value)
    lines.append('--------------------\n')
    lines += traceback.format_exception(etype, value, tb)
    msg = ''.join(lines)
    msg = msg.decode(sys.getfilesystemencoding(), "replace")
    _error_callback(msg)

class OutputToConsole:
    def __init__(self, prefix):
        self.prefix = unicode(prefix)
        self.buffer = ""
    def write(self, buf):
        import sys
        for line in buf.splitlines(True):
            self.buffer += line
            if self.buffer.endswith('\n'):
                msg = self.buffer.rstrip().decode(sys.getfilesystemencoding(), "replace")
                _error_callback(self.prefix + msg)
                self.buffer = ""

@ffi.def_extern(onerror=signal_error)
def pyunityvr_init(error_callback, *fns):
    import os, sys
    global _init_called, _main, _error_callback
    _error_callback = error_callback
    if _init_called:
        # not the first time: kill all modules that live inside
        # the same directory as 'main' or a subdirectory
        import main
        for sep in [os.sep, os.altsep]:
            basedir = os.path.dirname(main.__file__) + sep
            for key, module in sys.modules.items():
                path = getattr(module, '__file__', '')
                if path.startswith(basedir):
                    del sys.modules[key]
        # if the PyUnityVR package is also here, then it has been
        # killed too and will be reloaded by the next 'import'.
        # Otherwise, we must reset _init_called to False here.
        _init_called = False
        from PyUnityVR import ffi_interface
        ffi_interface.pyunityvr_init(error_callback, *fns)
    else:
        _init_called = "in-progress"
        sys.stdout = OutputToConsole(prefix="INFO:")
        sys.stderr = OutputToConsole(prefix="")
        import main
        _main = main.init(ffi, *fns)
        if _main is None:
            _main = main
        _init_called = True
    return 42

@ffi.def_extern(onerror=signal_error)
def pyunityvr_frame(num_controllers, controllers):
    _main.handle_frame(num_controllers, controllers)
    return 42

@ffi.def_extern(onerror=signal_error)
def pyunityvr_click(id):
    _main.handle_click(ffi.string(id))
    return 42