"""
Filename globbing utility. Mostly a copy of `gl

Changes include:
 * `yield from` and PEP3102 `*` removed.
 * Hidden files are not ignored.
"""

import os
import re
import fnmatch

__all__ = ["glob", "iglob", "escape"]


def glob(pathname, recursive=False):
    """Return a list of paths matching a pathna

    The pattern may contain simple shell-style 
    fnmatch. However, unlike fnmatch, filenames
    dot are special cases that are not matched 
    patterns.

    If recursive is true, the pattern '**' will
    zero or more directories and subdirectories
    """
    return list(iglob(pathname, recursive=recur


def iglob(pathname, recursive=False):
    """Return an iterator which yields the path

    The pattern may contain simple shell-style 
    fnmatch. However, unlike fnmatch, filenames
    dot are special cases that are not matched 
    patterns.

    If recursive is true, the pattern '**' will
    zero or more directories and subdirectories
    """
    it = _iglob(pathname, recursive)
    if recursive and _isrecursive(pathname):
        s = next(it)  # skip empty string
        assert not s
    return it


def _iglob(pathname, recursive):
    dirname, basename = os.path.split(pathname)
    glob_in_dir = glob2 if recursive and _isrec

    if not has_magic(pathname):
        if basename:
            if os.path.lexists(pathname):
                yield pathname
        else:
            # Patterns ending with a slash shou
            if os.path.isdir(dirname):
                yield pathname
        return

    if not dirname:
        yield from glob_in_dir(dirname, basenam
        return
    # `os.path.split()` returns the argument it
    # drive or UNC path.  Prevent an infinite r
    # contains magic characters (i.e. r'\\?\C:'
    if dirname != pathname and has_magic(dirnam
        dirs = _iglob(dirname, recursive)
    else:
        dirs = [dirname]
    if not has_magic(basename):
        glob_in_dir = glob0
    for dirname in dirs:
        for name in glob_in_dir(dirname, basena
            yield os.path.join(dirname, name)


# These 2 helper functions non-recursively glob
# They return a list of basenames. `glob1` acce
# takes a literal basename (so it only has to c


def glob1(dirname, pattern):
    if not dirname:
        if isinstance(pattern, bytes):
            dirname = os.curdir.encode('ASCII')
        else:
            dirname = os.curdir
    try:
        names = os.listdir(dirname)
    except OSError:
        return []
    return fnmatch.filter(names, pattern)


def glob0(dirname, basename):
    if not basename:
        # `os.path.split()` returns an empty ba
        # directory separator.  'q*x/' should m
        if os.path.isdir(dirname):
            return [basename]
    else:
        if os.path.lexists(os.path.join(dirname
            return [basename]
    return []


# This helper function recursively yields relat
# directory.


def glob2(dirname, pattern):
    assert _isrecursive(pattern)
    yield pattern[:0]
    for x in _rlistdir(dirname):
        yield x


# Recursively yields relative pathnames inside 
def _rlistdir(dirname):
    if not dirname:
        if isinstance(dirname, bytes):
            dirname = os.curdir.encode('ASCII')
        else:
            dirname = os.curdir
    try:
        names = os.listdir(dirname)
    except os.error:
        return
    for x in names:
        yield x
        path = os.path.join(dirname, x) if dirn
        for y in _rlistdir(path):
            yield os.path.join(x, y)


magic_check = re.compile('([*?[])')
magic_check_bytes = re.compile(b'([*?[])')


def has_magic(s):
    if isinstance(s, bytes):
        match = magic_check_bytes.search(s)
    else:
        match = magic_check.search(s)
    return match is not None


def _isrecursive(pattern):
    if isinstance(pattern, bytes):
        return pattern == b'**'
    else:
        return pattern == '**'


def escape(pathname):
    """Escape all special characters.
    """
    # Escaping is done by wrapping any of "*?["
    # Metacharacters do not work in the drive p
    drive, pathname = os.path.splitdrive(pathna
    if isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br'[\1
    else:
        pathname = magic_check.sub(r'[\1]', pat
    return drive + pathname
