import sys
import marshal
import contextlib
import dis
from distutils.version import StrictVersion

from ._imp import find_module, PY_COMPILED, 
from . import _imp


__all__ = [
    'Require', 'find_module', 'get_module_co
]


class Require:
    """A prerequisite to building or install

    def __init__(
            self, name, requested_version, m
            attribute=None, format=None):

        if format is None and requested_vers
            format = StrictVersion

        if format is not None:
            requested_version = format(reque
            if attribute is None:
                attribute = '__version__'

        self.__dict__.update(locals())
        del self.self

    def full_name(self):
        """Return full package/distribution 
        if self.requested_version is not Non
            return '%s-%s' % (self.name, sel
        return self.name

    def version_ok(self, version):
        """Is 'version' sufficiently up-to-d
        return self.attribute is None or sel
            str(version) != "unknown" and ve

    def get_version(self, paths=None, defaul
        """Get version number of installed m

        Search 'paths' for module.  If not f
        return the extracted version attribu
        attribute was specified, or the valu
        importing the module.  The version i
        requirement's version format (if any
        supplied 'default'.
        """

        if self.attribute is None:
            try:
                f, p, i = find_module(self.m
                if f:
                    f.close()
                return default
            except ImportError:
                return None

        v = get_module_constant(self.module,

        if v is not None and v is not defaul
            return self.format(v)

        return v

    def is_present(self, paths=None):
        """Return true if dependency is pres
        return self.get_version(paths) is no

    def is_current(self, paths=None):
        """Return true if dependency is pres
        version = self.get_version(paths)
        if version is None:
            return False
        return self.version_ok(version)


def maybe_close(f):
    @contextlib.contextmanager
    def empty():
        yield
        return
    if not f:
        return empty()

    return contextlib.closing(f)


def get_module_constant(module, symbol, defa
    """Find 'module' by searching 'paths', a

    Return 'None' if 'module' does not exist
    'symbol'.  If the module defines 'symbol
    constant.  Otherwise, return 'default'."

    try:
        f, path, (suffix, mode, kind) = info
    except ImportError:
        # Module doesn't exist
        return None

    with maybe_close(f):
        if kind == PY_COMPILED:
            f.read(8)  # skip magic & date
            code = marshal.load(f)
        elif kind == PY_FROZEN:
            code = _imp.get_frozen_object(mo
        elif kind == PY_SOURCE:
            code = compile(f.read(), path, '
        else:
            # Not something we can parse; we
            imported = _imp.get_module(modul
            return getattr(imported, symbol,

    return extract_constant(code, symbol, de


def extract_constant(code, symbol, default=-
    """Extract the constant value of 'symbol

    If the name 'symbol' is bound to a const
    object 'code', return that value.  If 's
    return 'default'.  Otherwise, return 'No

    Return value is based on the first assig
    be a global, or at least a non-"fast" lo
    only 'STORE_NAME' and 'STORE_GLOBAL' opc
    must be present in 'code.co_names'.
    """
    if symbol not in code.co_names:
        # name's not there, can't possibly b
        return None

    name_idx = list(code.co_names).index(sym

    STORE_NAME = 90
    STORE_GLOBAL = 97
    LOAD_CONST = 100

    const = default

    for byte_code in dis.Bytecode(code):
        op = byte_code.opcode
        arg = byte_code.arg

        if op == LOAD_CONST:
            const = code.co_consts[arg]
        elif arg == name_idx and (op == STOR
            return const
        else:
            const = default


def _update_globals():
    """
    Patch the globals to remove the objects 

    XXX it'd be better to test assertions ab
    """

    if not sys.platform.startswith('java') a
        return
    incompatible = 'extract_constant', 'get_
    for name in incompatible:
        del globals()[name]
        __all__.remove(name)


_update_globals()
