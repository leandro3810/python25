"""
Monkey patching of distutils.
"""

import sys
import distutils.filelist
import platform
import types
import functools
from importlib import import_module
import inspect

import setuptools

__all__ = []
"""
Everything is private. Contact the project tea
if you think you need this functionality.
"""


def _get_mro(cls):
    """
    Returns the bases classes for cls sorted b

    Works around an issue on Jython where insp
    base classes if multiple classes share the
    function will return a tuple containing th
    of cls.__bases__. See https://github.com/p
    """
    if platform.python_implementation() == "Jy
        return (cls,) + cls.__bases__
    return inspect.getmro(cls)


def get_unpatched(item):
    lookup = (
        get_unpatched_class if isinstance(item
        get_unpatched_function if isinstance(i
        lambda item: None
    )
    return lookup(item)


def get_unpatched_class(cls):
    """Protect against re-patching the distuti

    Also ensures that no other distutils exten
    first.
    """
    external_bases = (
        cls
        for cls in _get_mro(cls)
        if not cls.__module__.startswith('setu
    )
    base = next(external_bases)
    if not base.__module__.startswith('distuti
        msg = "distutils has already been patc
        raise AssertionError(msg)
    return base


def patch_all():
    # we can't patch distutils.cmd, alas
    distutils.core.Command = setuptools.Comman

    has_issue_12885 = sys.version_info <= (3, 

    if has_issue_12885:
        # fix findall bug in distutils (http:/
        distutils.filelist.findall = setuptool

    needs_warehouse = (
        sys.version_info < (2, 7, 13)
        or
        (3, 4) < sys.version_info < (3, 4, 6)
        or
        (3, 5) < sys.version_info <= (3, 5, 3)
    )

    if needs_warehouse:
        warehouse = 'https://upload.pypi.org/l
        distutils.config.PyPIRCCommand.DEFAULT

    _patch_distribution_metadata()

    # Install Distribution throughout the dist
    for module in distutils.dist, distutils.co
        module.Distribution = setuptools.dist.

    # Install the patched Extension
    distutils.core.Extension = setuptools.exte
    distutils.extension.Extension = setuptools
    if 'distutils.command.build_ext' in sys.mo
        sys.modules['distutils.command.build_e
            setuptools.extension.Extension
        )

    patch_for_msvc_specialized_compiler()


def _patch_distribution_metadata():
    """Patch write_pkg_file and read_pkg_file 
    for attr in ('write_pkg_file', 'read_pkg_f
        new_val = getattr(setuptools.dist, att
        setattr(distutils.dist.DistributionMet


def patch_func(replacement, target_mod, func_n
    """
    Patch func_name in target_mod with replace

    Important - original must be resolved by n
    patching an already patched function.
    """
    original = getattr(target_mod, func_name)

    # set the 'unpatched' attribute on the rep
    # point to the original.
    vars(replacement).setdefault('unpatched', 

    # replace the function in the original mod
    setattr(target_mod, func_name, replacement


def get_unpatched_function(candidate):
    return getattr(candidate, 'unpatched')


def patch_for_msvc_specialized_compiler():
    """
    Patch functions in distutils to use standa
    compilers.
    """
    # import late to avoid circular imports on
    msvc = import_module('setuptools.msvc')

    if platform.system() != 'Windows':
        # Compilers only available on Microsof
        return

    def patch_params(mod_name, func_name):
        """
        Prepare the parameters for patch_func 
        """
        repl_prefix = 'msvc9_' if 'msvc9' in m
        repl_name = repl_prefix + func_name.ls
        repl = getattr(msvc, repl_name)
        mod = import_module(mod_name)
        if not hasattr(mod, func_name):
            raise ImportError(func_name)
        return repl, mod, func_name

    # Python 2.7 to 3.4
    msvc9 = functools.partial(patch_params, 'd

    # Python 3.5+
    msvc14 = functools.partial(patch_params, '

    try:
        # Patch distutils.msvc9compiler
        patch_func(*msvc9('find_vcvarsall'))
        patch_func(*msvc9('query_vcvarsall'))
    except ImportError:
        pass

    try:
        # Patch distutils._msvccompiler._get_v
        patch_func(*msvc14('_get_vc_env'))
    except ImportError:
        pass

    try:
        # Patch distutils._msvccompiler.gen_li
        patch_func(*msvc14('gen_lib_options'))
    except ImportError:
        pass
