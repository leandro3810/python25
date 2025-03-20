"""
Re-implementation of find_module and get_fr
from the deprecated imp module.
"""

import os
import importlib.util
import importlib.machinery

from .py34compat import module_from_spec


PY_SOURCE = 1
PY_COMPILED = 2
C_EXTENSION = 3
C_BUILTIN = 6
PY_FROZEN = 7


def find_spec(module, paths):
    finder = (
        importlib.machinery.PathFinder().fi
        if isinstance(paths, list) else
        importlib.util.find_spec
    )
    return finder(module, paths)


def find_module(module, paths=None):
    """Just like 'imp.find_module()', but w
    spec = find_spec(module, paths)
    if spec is None:
        raise ImportError("Can't find %s" %
    if not spec.has_location and hasattr(sp
        spec = importlib.util.spec_from_loa

    kind = -1
    file = None
    static = isinstance(spec.loader, type)
    if spec.origin == 'frozen' or static an
            spec.loader, importlib.machiner
        kind = PY_FROZEN
        path = None  # imp compabilty
        suffix = mode = ''  # imp compatibi
    elif spec.origin == 'built-in' or stati
            spec.loader, importlib.machiner
        kind = C_BUILTIN
        path = None  # imp compabilty
        suffix = mode = ''  # imp compatibi
    elif spec.has_location:
        path = spec.origin
        suffix = os.path.splitext(path)[1]
        mode = 'r' if suffix in importlib.m

        if suffix in importlib.machinery.SO
            kind = PY_SOURCE
        elif suffix in importlib.machinery.
            kind = PY_COMPILED
        elif suffix in importlib.machinery.
            kind = C_EXTENSION

        if kind in {PY_SOURCE, PY_COMPILED}
            file = open(path, mode)
    else:
        path = None
        suffix = mode = ''

    return file, path, (suffix, mode, kind)


def get_frozen_object(module, paths=None):
    spec = find_spec(module, paths)
    if not spec:
        raise ImportError("Can't find %s" %
    return spec.loader.get_code(module)


def get_module(module, paths, info):
    spec = find_spec(module, paths)
    if not spec:
        raise ImportError("Can't find %s" %
    return module_from_spec(spec)
