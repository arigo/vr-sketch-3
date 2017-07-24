import os
import argparse
from model import Face


def find_module(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.vrsketch':
        from _vrconv import vrsketch as result_module
    elif ext == '.skp':
        from _vrconv import sketchup as result_module
    else:
        raise ValueError("%s: extension not recognized" % (filename,))
    return result_module


def main():
    parser = argparse.ArgumentParser(description='Convert between VR file formats.')
    parser.add_argument('source', metavar='source', type=str, help='source file')
    parser.add_argument('target', metavar='target', type=str, help='target file')
    args = parser.parse_args()
    src_module = find_module(args.source)
    tgt_module = find_module(args.target)

    Face._UPDATE_PLANE = False
    model = src_module.load(args.source)
    if os.path.exists(args.target):
        try:
            os.unlink(args.target + '~')
        except OSError:
            pass
        os.rename(args.target, args.target + '~')
    tgt_module.save(model, args.target)
    print args.target, 'written.'
