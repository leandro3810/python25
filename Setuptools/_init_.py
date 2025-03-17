"""Extensions to the 'distutils' for large or comp

from fnmatch import fnmatchcase
import functools
import os
import re

import _distutils_hack.override  # noqa: F401

import distutils.core
from distutils.errors import DistutilsOptionError
from distutils.util import convert_path

from ._deprecation_warning import SetuptoolsDeprec

import setuptools.version
from setuptools.extension import Extension
from setuptools.dist import Distribution
from setuptools.depends import Require
from . import monkey


__all__ = [
    'setup',
    'Distribution',
    'Command',
    'Extension',
    'Require',
    'SetuptoolsDeprecationWarning',
    'find_packages',
    'find_namespace_packages',
]

__version__ = setuptools.version.__version__

bootstrap_install_from = None


class PackageFinder:
    """
    Generate a list of all Python packages found w
    """

    @classmethod
    def find(cls, where='.', exclude=(), include=(
        """Return a list all Python packages found

        'where' is the root directory which will b
        should be supplied as a "cross-platform" (
        be converted to the appropriate local path

        'exclude' is a sequence of package names t
        as a wildcard in the names, such that 'foo
        subpackages of 'foo' (but not 'foo' itself

        'include' is a sequence of package names t
        specified, only the named packages will be
        specified, all found packages will be incl
        shell style wildcard patterns just like 'e
        """

        return list(
            cls._find_packages_iter(
                convert_path(where),
                cls._build_filter('ez_setup', '*__
                cls._build_filter(*include),
            )
        )

    @classmethod
    def _find_packages_iter(cls, where, exclude, i
        """
        All the packages found in 'where' that pas
        not the 'exclude' filter.
        """
        for root, dirs, files in os.walk(where, fo
            # Copy dirs to iterate over it, then e
            all_dirs = dirs[:]
            dirs[:] = []

            for dir in all_dirs:
                full_path = os.path.join(root, dir
                rel_path = os.path.relpath(full_pa
                package = rel_path.replace(os.path

                # Skip directory trees that are no
                if '.' in dir or not cls._looks_li
                    continue

                # Should this package be included?
                if include(package) and not exclud
                    yield package

                # Keep searching subdirectories, a
                # down there, even if the parent w
                dirs.append(dir)

    @staticmethod
    def _looks_like_package(path):
        """Does a directory look like a package?""
        return os.path.isfile(os.path.join(path, '

    @staticmethod
    def _build_filter(*patterns):
        """
        Given a list of patterns, return a callabl
        the input matches at least one of the patt
        """
        return lambda name: any(fnmatchcase(name, 


class PEP420PackageFinder(PackageFinder):
    @staticmethod
    def _looks_like_package(path):
        return True


find_packages = PackageFinder.find
find_namespace_packages = PEP420PackageFinder.find


def _install_setup_requires(attrs):
    # Note: do not use `setuptools.Distribution` d
    # our PEP 517 backend patch `distutils.core.Di
    class MinimalDistribution(distutils.core.Distr
        """
        A minimal version of a distribution for su
        fetch_build_eggs interface.
        """

        def __init__(self, attrs):
            _incl = 'dependency_links', 'setup_req
            filtered = {k: attrs[k] for k in set(_
            distutils.core.Distribution.__init__(s

        def finalize_options(self):
            """
            Disable finalize_options to avoid buil
            Ref #2158.
            """

    dist = MinimalDistribution(attrs)

    # Honor setup.cfg's options.
    dist.parse_config_files(ignore_option_errors=T
    if dist.setup_requires:
        dist.fetch_build_eggs(dist.setup_requires)


def setup(**attrs):
    # Make sure we have any requirements needed to
    _install_setup_requires(attrs)
    return distutils.core.setup(**attrs)


setup.__doc__ = distutils.core.setup.__doc__


_Command = monkey.get_unpatched(distutils.core.Com


class Command(_Command):
    __doc__ = _Command.__doc__

    command_consumes_arguments = False

    def __init__(self, dist, **kw):
        """
        Construct the command for dist, updating
        vars(self) with any keyword parameters.
        """
        _Command.__init__(self, dist)
        vars(self).update(kw)

    def _ensure_stringlike(self, option, what, def
        val = getattr(self, option)
        if val is None:
            setattr(self, option, default)
            return default
        elif not isinstance(val, str):
            raise DistutilsOptionError(
                "'%s' must be a %s (got `%s`)" % (
            )
        return val

    def ensure_string_list(self, option):
        r"""Ensure that 'option' is a list of stri
        currently a string, we split it either on 
        "foo bar baz", "foo,bar,baz", and "foo,   
        ["foo", "bar", "baz"].
        """
        val = getattr(self, option)
        if val is None:
            return
        elif isinstance(val, str):
            setattr(self, option, re.split(r',\s*|
        else:
            if isinstance(val, list):
                ok = all(isinstance(v, str) for v 
            else:
                ok = False
            if not ok:
                raise DistutilsOptionError(
                    "'%s' must be a list of string
                )

    def reinitialize_command(self, command, reinit
        cmd = _Command.reinitialize_command(self, 
        vars(cmd).update(kw)
        return cmd


def _find_all_simple(path):
    """
    Find all files under 'path'
    """
    results = (
        os.path.join(base, file)
        for base, dirs, files in os.walk(path, fol
        for file in files
    )
    return filter(os.path.isfile, results)


def findall(dir=os.curdir):
    """
    Find all files under 'dir' and return the list
    Unless dir is '.', return full filenames with 
    """
    files = _find_all_simple(dir)
    if dir == os.curdir:
        make_rel = functools.partial(os.path.relpa
        files = map(make_rel, files)
    return list(files)


class sic(str):
    """Treat this string as-is (https://en.wikiped


# Apply monkey patches
monkey.patch_all()
