import re
import functools
import distutils.core
import distutils.errors
import distutils.extension

from .monkey import get_unpatched


def _have_cython():
    """
    Return True if Cython can be imported.
    """
    cython_impl = 'Cython.Distutils.build_ext'
    try:
        # from (cython_impl) import build_ext
        __import__(cython_impl, fromlist=['build
        return True
    except Exception:
        pass
    return False


# for compatibility
have_pyrex = _have_cython

_Extension = get_unpatched(distutils.core.Extens


class Extension(_Extension):
    """Extension that uses '.c' files in place o

    def __init__(self, name, sources, *args, **k
        # The *args is needed for compatibility 
        # arguments. py_limited_api may be set o
        self.py_limited_api = kw.pop("py_limited
        _Extension.__init__(self, name, sources,

    def _convert_pyx_sources_to_lang(self):
        """
        Replace sources with .pyx extensions to 
        language extension. This mechanism allow
        pre-converted sources but to prefer the 
        """
        if _have_cython():
            # the build has Cython, so allow it 
            return
        lang = self.language or ''
        target_ext = '.cpp' if lang.lower() == '
        sub = functools.partial(re.sub, '.pyx$',
        self.sources = list(map(sub, self.source


class Library(Extension):
    """Just like a regular Extension, but built 
