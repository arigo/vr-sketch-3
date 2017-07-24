import os
from app import App, initialize_functions


INITIAL_FILENAME = os.path.abspath(
    os.path.join(u"Documents", u"NoName.vrsketch"))


def init(ffi, *fns):
    initialize_functions(ffi, *fns)
    return App(INITIAL_FILENAME)
