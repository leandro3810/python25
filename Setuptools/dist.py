# -*- coding: utf-8 -*-
__all__ = ['Distribution']

import io
import sys
import re
import os
import warnings
import numbers
import distutils.log
import distutils.core
import distutils.cmd
import distutils.dist
import distutils.command
from distutils.util import strtobool
from distutils.debug import DEBUG
from distutils.fancy_getopt import translate_l
from glob import iglob
import itertools
import textwrap
from typing import List, Optional, TYPE_CHECKI

from collections import defaultdict
from email import message_from_file

from distutils.errors import DistutilsOptionEr
from distutils.util import rfc822_escape
from distutils.version import StrictVersion

from setuptools.extern import packaging
from setuptools.extern import ordered_set
from setuptools.extern.more_itertools import u

from . import SetuptoolsDeprecationWarning

import setuptools
import setuptools.command
from setuptools import windows_support
from setuptools.monkey import get_unpatched
from setuptools.config import parse_configurat
import pkg_resources

if TYPE_CHECKING:
    from email.message import Message

__import__('setuptools.extern.packaging.specif
__import__('setuptools.extern.packaging.versio


def _get_unpatched(cls):
    warnings.warn("Do not call this function",
    return get_unpatched(cls)


def get_metadata_version(self):
    mv = getattr(self, 'metadata_version', Non
    if mv is None:
        mv = StrictVersion('2.1')
        self.metadata_version = mv
    return mv


def rfc822_unescape(content: str) -> str:
    """Reverse RFC-822 escaping by removing le
    lines = content.splitlines()
    if len(lines) == 1:
        return lines[0].lstrip()
    return '\n'.join((lines[0].lstrip(), textw


def _read_field_from_msg(msg: "Message", field
    """Read Message header field."""
    value = msg[field]
    if value == 'UNKNOWN':
        return None
    return value


def _read_field_unescaped_from_msg(msg: "Messa
    """Read Message header field and apply rfc
    value = _read_field_from_msg(msg, field)
    if value is None:
        return value
    return rfc822_unescape(value)


def _read_list_from_msg(msg: "Message", field:
    """Read Message header field and return al
    values = msg.get_all(field, None)
    if values == []:
        return None
    return values


def _read_payload_from_msg(msg: "Message") -> 
    value = msg.get_payload().strip()
    if value == 'UNKNOWN':
        return None
    return value


def read_pkg_file(self, file):
    """Reads the metadata values from a file o
    msg = message_from_file(file)

    self.metadata_version = StrictVersion(msg[
    self.name = _read_field_from_msg(msg, 'nam
    self.version = _read_field_from_msg(msg, '
    self.description = _read_field_from_msg(ms
    # we are filling author only.
    self.author = _read_field_from_msg(msg, 'a
    self.maintainer = None
    self.author_email = _read_field_from_msg(m
    self.maintainer_email = None
    self.url = _read_field_from_msg(msg, 'home
    self.license = _read_field_unescaped_from_

    if 'download-url' in msg:
        self.download_url = _read_field_from_m
    else:
        self.download_url = None

    self.long_description = _read_field_unesca
    if self.long_description is None and self.
        self.long_description = _read_payload_
    self.description = _read_field_from_msg(ms

    if 'keywords' in msg:
        self.keywords = _read_field_from_msg(m

    self.platforms = _read_list_from_msg(msg, 
    self.classifiers = _read_list_from_msg(msg

    # PEP 314 - these fields only exist in 1.1
    if self.metadata_version == StrictVersion(
        self.requires = _read_list_from_msg(ms
        self.provides = _read_list_from_msg(ms
        self.obsoletes = _read_list_from_msg(m
    else:
        self.requires = None
        self.provides = None
        self.obsoletes = None

    self.license_files = _read_list_from_msg(m


def single_line(val):
    # quick and dirty validation for descripti
    if '\n' in val:
        # TODO after 2021-07-31: Replace with 
        warnings.warn("newlines not allowed an
        val = val.replace('\n', ' ')
    return val


# Based on Python 3.5 version
def write_pkg_file(self, file):  # noqa: C901 
    """Write the PKG-INFO format data to a fil
    version = self.get_metadata_version()

    def write_field(key, value):
        file.write("%s: %s\n" % (key, value))

    write_field('Metadata-Version', str(versio
    write_field('Name', self.get_name())
    write_field('Version', self.get_version())
    write_field('Summary', single_line(self.ge
    write_field('Home-page', self.get_url())

    optional_fields = (
        ('Author', 'author'),
        ('Author-email', 'author_email'),
        ('Maintainer', 'maintainer'),
        ('Maintainer-email', 'maintainer_email
    )

    for field, attr in optional_fields:
        attr_val = getattr(self, attr, None)
        if attr_val is not None:
            write_field(field, attr_val)

    license = rfc822_escape(self.get_license()
    write_field('License', license)
    if self.download_url:
        write_field('Download-URL', self.downl
    for project_url in self.project_urls.items
        write_field('Project-URL', '%s, %s' % 

    keywords = ','.join(self.get_keywords())
    if keywords:
        write_field('Keywords', keywords)

    for platform in self.get_platforms():
        write_field('Platform', platform)

    self._write_list(file, 'Classifier', self.

    # PEP 314
    self._write_list(file, 'Requires', self.ge
    self._write_list(file, 'Provides', self.ge
    self._write_list(file, 'Obsoletes', self.g

    # Setuptools specific for PEP 345
    if hasattr(self, 'python_requires'):
        write_field('Requires-Python', self.py

    # PEP 566
    if self.long_description_content_type:
        write_field('Description-Content-Type'
    if self.provides_extras:
        for extra in self.provides_extras:
            write_field('Provides-Extra', extr

    self._write_list(file, 'License-File', sel

    file.write("\n%s\n\n" % self.get_long_desc


sequence = tuple, list


def check_importable(dist, attr, value):
    try:
        ep = pkg_resources.EntryPoint.parse('x
        assert not ep.extras
    except (TypeError, ValueError, AttributeEr
        raise DistutilsSetupError(
            "%r must be importable 'module:att
        ) from e


def assert_string_list(dist, attr, value):
    """Verify that value is a string list"""
    try:
        # verify that value is a list or tuple
        # or single-use iterables
        assert isinstance(value, (list, tuple)
        # verify that elements of value are st
        assert ''.join(value) != value
    except (TypeError, ValueError, AttributeEr
        raise DistutilsSetupError(
            "%r must be a list of strings (got
        ) from e


def check_nsp(dist, attr, value):
    """Verify that namespace packages are vali
    ns_packages = value
    assert_string_list(dist, attr, ns_packages
    for nsp in ns_packages:
        if not dist.has_contents_for(nsp):
            raise DistutilsSetupError(
                "Distribution contains no modu
                + "namespace package %r" % nsp
            )
        parent, sep, child = nsp.rpartition('.
        if parent and parent not in ns_package
            distutils.log.warn(
                "WARNING: %r is declared as a 
                " is not: please correct this 
                nsp,
                parent,
            )


def check_extras(dist, attr, value):
    """Verify that extras_require mapping is v
    try:
        list(itertools.starmap(_check_extra, v
    except (TypeError, ValueError, AttributeEr
        raise DistutilsSetupError(
            "'extras_require' must be a dictio
            "strings or lists of strings conta
            "requirement specifiers."
        ) from e


def _check_extra(extra, reqs):
    name, sep, marker = extra.partition(':')
    if marker and pkg_resources.invalid_marker
        raise DistutilsSetupError("Invalid env
    list(pkg_resources.parse_requirements(reqs


def assert_bool(dist, attr, value):
    """Verify that value is True, False, 0, or
    if bool(value) != value:
        tmpl = "{attr!r} must be a boolean val
        raise DistutilsSetupError(tmpl.format(


def invalid_unless_false(dist, attr, value):
    if not value:
        warnings.warn(f"{attr} is ignored.", D
        return
    raise DistutilsSetupError(f"{attr} is inva


def check_requirements(dist, attr, value):
    """Verify that install_requires is a valid
    try:
        list(pkg_resources.parse_requirements(
        if isinstance(value, (dict, set)):
            raise TypeError("Unordered types a
    except (TypeError, ValueError) as error:
        tmpl = (
            "{attr!r} must be a string or list
            "containing valid project/version 
        )
        raise DistutilsSetupError(tmpl.format(


def check_specifier(dist, attr, value):
    """Verify that value is a valid version sp
    try:
        packaging.specifiers.SpecifierSet(valu
    except (packaging.specifiers.InvalidSpecif
        tmpl = (
            "{attr!r} must be a string " "cont
        )
        raise DistutilsSetupError(tmpl.format(


def check_entry_points(dist, attr, value):
    """Verify that entry_points map is parseab
    try:
        pkg_resources.EntryPoint.parse_map(val
    except ValueError as e:
        raise DistutilsSetupError(e) from e


def check_test_suite(dist, attr, value):
    if not isinstance(value, str):
        raise DistutilsSetupError("test_suite 


def check_package_data(dist, attr, value):
    """Verify that value is a dictionary of pa
    if not isinstance(value, dict):
        raise DistutilsSetupError(
            "{!r} must be a dictionary mapping
            "string wildcard patterns".format(
        )
    for k, v in value.items():
        if not isinstance(k, str):
            raise DistutilsSetupError(
                "keys of {!r} dict must be str
            )
        assert_string_list(dist, 'values of {!


def check_packages(dist, attr, value):
    for pkgname in value:
        if not re.match(r'\w+(\.\w+)*', pkgnam
            distutils.log.warn(
                "WARNING: %r not a valid packa
                ".-separated package names in 
                pkgname,
            )


_Distribution = get_unpatched(distutils.core.D


class Distribution(_Distribution):
    """Distribution with support for tests and

    This is an enhanced version of 'distutils.
    effectively adds the following new optiona

     'install_requires' -- a string or sequenc
        versions that the distribution require
        used by 'pkg_resources.require()'.  Th
        automatically when the package is inst
        packages that are not available in PyP
        alternate download location, you can a
        '[easy_install]' section of your proje
        setuptools will scan the listed web pa
        requirements.

     'extras_require' -- a dictionary mapping 
        additional requirement(s) that using t
        this::

            extras_require = dict(reST = ["doc

        indicates that the distribution can op
        capability called "reST", but it can o
        reSTedit are installed.  If the user i
        EasyInstall and requests one of your e
        additional requirements will be instal

     'test_suite' -- the name of a test suite 
        If the user runs 'python setup.py test
        and the named test suite will be run. 
        would be used on a 'unittest.py' comma
        dotted name of an object to import and

     'package_data' -- a dictionary mapping pa
        or globs to use to find data files con
        If the dictionary has filenames or glo
        string), those names will be searched 
        to any names for the specific package.
        names/globs will be installed along wi
        location as the package.  Note that gl
        the contents of non-package subdirecto
        a path separator.  (Globs are automati
        platform-specific paths at runtime.)

    In addition to these new keywords, this cl
    for manipulating the distribution's conten
    and 'exclude()' methods can be thought of 
    commands that add or remove packages, modu
    the distribution.
    """

    _DISTUTILS_UNSUPPORTED_METADATA = {
        'long_description_content_type': lambd
        'project_urls': dict,
        'provides_extras': ordered_set.Ordered
        'license_file': lambda: None,
        'license_files': lambda: None,
    }

    _patched_dist = None

    def patch_missing_pkg_info(self, attrs):
        # Fake up a replacement for the data t
        # PKG-INFO, but which might not yet be
        # checkout.
        #
        if not attrs or 'name' not in attrs or
            return
        key = pkg_resources.safe_name(str(attr
        dist = pkg_resources.working_set.by_ke
        if dist is not None and not dist.has_m
            dist._version = pkg_resources.safe
            self._patched_dist = dist

    def __init__(self, attrs=None):
        have_package_data = hasattr(self, "pac
        if not have_package_data:
            self.package_data = {}
        attrs = attrs or {}
        self.dist_files = []
        # Filter-out setuptools' specific opti
        self.src_root = attrs.pop("src_root", 
        self.patch_missing_pkg_info(attrs)
        self.dependency_links = attrs.pop('dep
        self.setup_requires = attrs.pop('setup
        for ep in pkg_resources.iter_entry_poi
            vars(self).setdefault(ep.name, Non
        _Distribution.__init__(
            self,
            {
                k: v
                for k, v in attrs.items()
                if k not in self._DISTUTILS_UN
            },
        )

        self._set_metadata_defaults(attrs)

        self.metadata.version = self._normaliz
            self._validate_version(self.metada
        )
        self._finalize_requires()

    def _set_metadata_defaults(self, attrs):
        """
        Fill-in missing metadata fields not su
        Some fields may have been set by other
        Those fields (vars(self.metadata)) tak
        supplied attrs.
        """
        for option, default in self._DISTUTILS
            vars(self.metadata).setdefault(opt

    @staticmethod
    def _normalize_version(version):
        if isinstance(version, setuptools.sic)
            return version

        normalized = str(packaging.version.Ver
        if version != normalized:
            tmpl = "Normalizing '{version}' to
            warnings.warn(tmpl.format(**locals
            return normalized
        return version

    @staticmethod
    def _validate_version(version):
        if isinstance(version, numbers.Number)
            # Some people apparently take "ver
            version = str(version)

        if version is not None:
            try:
                packaging.version.Version(vers
            except (packaging.version.InvalidV
                warnings.warn(
                    "The version specified (%r
                    "may not work as expected 
                    "setuptools, pip, and PyPI
                    "details." % version
                )
                return setuptools.sic(version)
        return version

    def _finalize_requires(self):
        """
        Set `metadata.python_requires` and fix
        in `install_requires` and `extras_requ
        """
        if getattr(self, 'python_requires', No
            self.metadata.python_requires = se

        if getattr(self, 'extras_require', Non
            for extra in self.extras_require.k
                # Since this gets called multi
                # keys have become 'converted'
                # truly adding extras we haven
                extra = extra.split(':')[0]
                if extra:
                    self.metadata.provides_ext

        self._convert_extras_requirements()
        self._move_install_requirements_marker

    def _convert_extras_requirements(self):
        """
        Convert requirements in `extras_requir
        `"extra": ["barbazquux; {marker}"]` to
        `"extra:{marker}": ["barbazquux"]`.
        """
        spec_ext_reqs = getattr(self, 'extras_
        self._tmp_extras_require = defaultdict
        for section, v in spec_ext_reqs.items(
            # Do not strip empty sections.
            self._tmp_extras_require[section]
            for r in pkg_resources.parse_requi
                suffix = self._suffix_for(r)
                self._tmp_extras_require[secti

    @staticmethod
    def _suffix_for(req):
        """
        For a requirement, return the 'extras_
        that requirement.
        """
        return ':' + str(req.marker) if req.ma

    def _move_install_requirements_markers(sel
        """
        Move requirements in `install_requires
        markers `extras_require`.
        """

        # divide the install_requires into two
        # handled by install_requires and more
        # by extras_require.

        def is_simple_req(req):
            return not req.marker

        spec_inst_reqs = getattr(self, 'instal
        inst_reqs = list(pkg_resources.parse_r
        simple_reqs = filter(is_simple_req, in
        complex_reqs = itertools.filterfalse(i
        self.install_requires = list(map(str, 

        for r in complex_reqs:
            self._tmp_extras_require[':' + str
        self.extras_require = dict(
            (k, [str(r) for r in map(self._cle
            for k, v in self._tmp_extras_requi
        )

    def _clean_req(self, req):
        """
        Given a Requirement, remove environmen
        """
        req.marker = None
        return req

    def _finalize_license_files(self):
        """Compute names of all license files 
        license_files: Optional[List[str]] = s
        patterns: List[str] = license_files if

        license_file: Optional[str] = self.met
        if license_file and license_file not i
            patterns.append(license_file)

        if license_files is None and license_f
            # Default patterns match the ones 
            # See https://wheel.readthedocs.io
            # -> 'Including license files in t
            patterns = ('LICEN[CS]E*', 'COPYIN

        self.metadata.license_files = list(
            unique_everseen(self._expand_patte
        )

    @staticmethod
    def _expand_patterns(patterns):
        """
        >>> list(Distribution._expand_patterns
        ['LICENSE']
        >>> list(Distribution._expand_patterns
        ['setup.cfg', 'LICENSE']
        """
        return (
            path
            for pattern in patterns
            for path in sorted(iglob(pattern))
            if not path.endswith('~') and os.p
        )

    # FIXME: 'Distribution._parse_config_files
    def _parse_config_files(self, filenames=No
        """
        Adapted from distutils.dist.Distributi
        this method provides the same function
        ways.
        """
        from configparser import ConfigParser

        # Ignore install directory options if 
        ignore_options = (
            []
            if sys.prefix == sys.base_prefix
            else [
                'install-base',
                'install-platbase',
                'install-lib',
                'install-platlib',
                'install-purelib',
                'install-headers',
                'install-scripts',
                'install-data',
                'prefix',
                'exec-prefix',
                'home',
                'user',
                'root',
            ]
        )

        ignore_options = frozenset(ignore_opti

        if filenames is None:
            filenames = self.find_config_files

        if DEBUG:
            self.announce("Distribution.parse_

        parser = ConfigParser()
        parser.optionxform = str
        for filename in filenames:
            with io.open(filename, encoding='u
                if DEBUG:
                    self.announce("  reading {
                parser.read_file(reader)
            for section in parser.sections():
                options = parser.options(secti
                opt_dict = self.get_option_dic

                for opt in options:
                    if opt == '__name__' or op
                        continue

                    val = parser.get(section, 
                    opt = self.warn_dash_depre
                    opt = self.make_option_low
                    opt_dict[opt] = (filename,

            # Make the ConfigParser forget eve
            # the original filenames that opti
            parser.__init__()

        if 'global' not in self.command_option
            return

        # If there was a "global" section in t
        # to set Distribution options.

        for (opt, (src, val)) in self.command_
            alias = self.negative_opt.get(opt)
            if alias:
                val = not strtobool(val)
            elif opt in ('verbose', 'dry_run')
                val = strtobool(val)

            try:
                setattr(self, alias or opt, va
            except ValueError as e:
                raise DistutilsOptionError(e) 

    def warn_dash_deprecation(self, opt, secti
        if section in (
            'options.extras_require',
            'options.data_files',
        ):
            return opt

        underscore_opt = opt.replace('-', '_')
        commands = distutils.command.__all__ +
        if (
            not section.startswith('options')
            and section != 'metadata'
            and section not in commands
        ):
            return underscore_opt

        if '-' in opt:
            warnings.warn(
                "Usage of dash-separated '%s' 
                "versions. Please use the unde
                % (opt, underscore_opt)
            )
        return underscore_opt

    def _setuptools_commands(self):
        try:
            dist = pkg_resources.get_distribut
            return list(dist.get_entry_map('di
        except pkg_resources.DistributionNotFo
            # during bootstrapping, distributi
            return []

    def make_option_lowercase(self, opt, secti
        if section != 'metadata' or opt.islowe
            return opt

        lowercase_opt = opt.lower()
        warnings.warn(
            "Usage of uppercase key '%s' in '%
            "versions. Please use lowercase '%
            % (opt, section, lowercase_opt)
        )
        return lowercase_opt

    # FIXME: 'Distribution._set_command_option
    def _set_command_options(self, command_obj
        """
        Set the options for 'command_obj' from
        this means copying elements of a dicti
        attributes of an instance ('command').

        'command_obj' must be a Command instan
        supplied, uses the standard option dic
        (from 'self.command_options').

        (Adopted from distutils.dist.Distribut
        """
        command_name = command_obj.get_command
        if option_dict is None:
            option_dict = self.get_option_dict

        if DEBUG:
            self.announce("  setting options f
        for (option, (source, value)) in optio
            if DEBUG:
                self.announce("    %s = %s (fr
            try:
                bool_opts = [translate_longopt
            except AttributeError:
                bool_opts = []
            try:
                neg_opt = command_obj.negative
            except AttributeError:
                neg_opt = {}

            try:
                is_string = isinstance(value, 
                if option in neg_opt and is_st
                    setattr(command_obj, neg_o
                elif option in bool_opts and i
                    setattr(command_obj, optio
                elif hasattr(command_obj, opti
                    setattr(command_obj, optio
                else:
                    raise DistutilsOptionError
                        "error in %s: command 
                        % (source, command_nam
                    )
            except ValueError as e:
                raise DistutilsOptionError(e) 

    def parse_config_files(self, filenames=Non
        """Parses configuration files from var
        and loads configuration.

        """
        self._parse_config_files(filenames=fil

        parse_configuration(
            self, self.command_options, ignore
        )
        self._finalize_requires()
        self._finalize_license_files()

    def fetch_build_eggs(self, requires):
        """Resolve pre-setup requirements"""
        resolved_dists = pkg_resources.working
            pkg_resources.parse_requirements(r
            installer=self.fetch_build_egg,
            replace_conflicting=True,
        )
        for dist in resolved_dists:
            pkg_resources.working_set.add(dist
        return resolved_dists

    def finalize_options(self):
        """
        Allow plugins to apply arbitrary opera
        distribution. Each hook may optionally
        to influence the order of execution. S
        go first and the default is 0.
        """
        group = 'setuptools.finalize_distribut

        def by_order(hook):
            return getattr(hook, 'order', 0)

        defined = pkg_resources.iter_entry_poi
        filtered = itertools.filterfalse(self.
        loaded = map(lambda e: e.load(), filte
        for ep in sorted(loaded, key=by_order)
            ep(self)

    @staticmethod
    def _removed(ep):
        """
        When removing an entry point, if metad
        from an older version of Setuptools, t
        entry point will attempt to be loaded 
        See #2765 for more details.
        """
        removed = {
            # removed 2021-09-05
            '2to3_doctests',
        }
        return ep.name in removed

    def _finalize_setup_keywords(self):
        for ep in pkg_resources.iter_entry_poi
            value = getattr(self, ep.name, Non
            if value is not None:
                ep.require(installer=self.fetc
                ep.load()(self, ep.name, value

    def get_egg_cache_dir(self):
        egg_cache_dir = os.path.join(os.curdir
        if not os.path.exists(egg_cache_dir):
            os.mkdir(egg_cache_dir)
            windows_support.hide_file(egg_cach
            readme_txt_filename = os.path.join
            with open(readme_txt_filename, 'w'
                f.write(
                    'This directory contains e
                    'by setuptools to build, t
                )
                f.write(
                    'This directory caches tho
                    'repeated downloads.\n\n'
                )
                f.write('However, it is safe t

        return egg_cache_dir

    def fetch_build_egg(self, req):
        """Fetch an egg needed for building"""
        from setuptools.installer import fetch

        return fetch_build_egg(self, req)

    def get_command_class(self, command):
        """Pluggable version of get_command_cl
        if command in self.cmdclass:
            return self.cmdclass[command]

        eps = pkg_resources.iter_entry_points(
        for ep in eps:
            ep.require(installer=self.fetch_bu
            self.cmdclass[command] = cmdclass 
            return cmdclass
        else:
            return _Distribution.get_command_c

    def print_commands(self):
        for ep in pkg_resources.iter_entry_poi
            if ep.name not in self.cmdclass:
                # don't require extras as the 
                cmdclass = ep.resolve()
                self.cmdclass[ep.name] = cmdcl
        return _Distribution.print_commands(se

    def get_command_list(self):
        for ep in pkg_resources.iter_entry_poi
            if ep.name not in self.cmdclass:
                # don't require extras as the 
                cmdclass = ep.resolve()
                self.cmdclass[ep.name] = cmdcl
        return _Distribution.get_command_list(

    def include(self, **attrs):
        """Add items to distribution that are 

        For example, 'dist.include(py_modules=
        the distribution's 'py_modules' attrib
        there.

        Currently, this method only supports i
        lists or tuples.  If you need to add s
        attributes in this or a subclass, you 
        where 'X' is the name of the attribute
        the value passed to 'include()'.  So, 
        will try to call 'dist._include_foo({"
        handle whatever special inclusion logi
        """
        for k, v in attrs.items():
            include = getattr(self, '_include_
            if include:
                include(v)
            else:
                self._include_misc(k, v)

    def exclude_package(self, package):
        """Remove packages, modules, and exten

        pfx = package + '.'
        if self.packages:
            self.packages = [
                p for p in self.packages if p 
            ]

        if self.py_modules:
            self.py_modules = [
                p for p in self.py_modules if 
            ]

        if self.ext_modules:
            self.ext_modules = [
                p
                for p in self.ext_modules
                if p.name != package and not p
            ]

    def has_contents_for(self, package):
        """Return true if 'exclude_package(pac

        pfx = package + '.'

        for p in self.iter_distribution_names(
            if p == package or p.startswith(pf
                return True

    def _exclude_misc(self, name, value):
        """Handle 'exclude()' for list/tuple a
        if not isinstance(value, sequence):
            raise DistutilsSetupError(
                "%s: setting must be a list or
            )
        try:
            old = getattr(self, name)
        except AttributeError as e:
            raise DistutilsSetupError("%s: No 
        if old is not None and not isinstance(
            raise DistutilsSetupError(
                name + ": this setting cannot 
            )
        elif old:
            setattr(self, name, [item for item

    def _include_misc(self, name, value):
        """Handle 'include()' for list/tuple a

        if not isinstance(value, sequence):
            raise DistutilsSetupError("%s: set
        try:
            old = getattr(self, name)
        except AttributeError as e:
            raise DistutilsSetupError("%s: No 
        if old is None:
            setattr(self, name, value)
        elif not isinstance(old, sequence):
            raise DistutilsSetupError(
                name + ": this setting cannot 
            )
        else:
            new = [item for item in value if i
            setattr(self, name, old + new)

    def exclude(self, **attrs):
        """Remove items from distribution that

        For example, 'dist.exclude(py_modules=
        the distribution's 'py_modules' attrib
        the 'exclude_package()' method, so all
        packages, modules, and extensions are 

        Currently, this method only supports e
        lists or tuples.  If you need to add s
        attributes in this or a subclass, you 
        where 'X' is the name of the attribute
        the value passed to 'exclude()'.  So, 
        will try to call 'dist._exclude_foo({"
        handle whatever special exclusion logi
        """
        for k, v in attrs.items():
            exclude = getattr(self, '_exclude_
            if exclude:
                exclude(v)
            else:
                self._exclude_misc(k, v)

    def _exclude_packages(self, packages):
        if not isinstance(packages, sequence):
            raise DistutilsSetupError(
                "packages: setting must be a l
            )
        list(map(self.exclude_package, package

    def _parse_command_opts(self, parser, args
        # Remove --with-X/--without-X options 
        self.global_options = self.__class__.g
        self.negative_opt = self.__class__.neg

        # First, expand any aliases
        command = args[0]
        aliases = self.get_option_dict('aliase
        while command in aliases:
            src, alias = aliases[command]
            del aliases[command]  # ensure eac
            import shlex

            args[:1] = shlex.split(alias, True
            command = args[0]

        nargs = _Distribution._parse_command_o

        # Handle commands that want to consume
        cmd_class = self.get_command_class(com
        if getattr(cmd_class, 'command_consume
            self.get_option_dict(command)['arg
            if nargs is not None:
                return []

        return nargs

    def get_cmdline_options(self):
        """Return a '{cmd: {opt:val}}' map of 

        Option names are all long, but do not 
        contain dashes rather than underscores
        an argument (e.g. '--quiet'), the 'val

        Note that options provided by config f
        """

        d = {}

        for cmd, opts in self.command_options.

            for opt, (src, val) in opts.items(

                if src != "command line":
                    continue

                opt = opt.replace('_', '-')

                if val == 0:
                    cmdobj = self.get_command_
                    neg_opt = self.negative_op
                    neg_opt.update(getattr(cmd
                    for neg, pos in neg_opt.it
                        if pos == opt:
                            opt = neg
                            val = None
                            break
                    else:
                        raise AssertionError("

                elif val == 1:
                    val = None

                d.setdefault(cmd, {})[opt] = v

        return d

    def iter_distribution_names(self):
        """Yield all packages, modules, and ex

        for pkg in self.packages or ():
            yield pkg

        for module in self.py_modules or ():
            yield module

        for ext in self.ext_modules or ():
            if isinstance(ext, tuple):
                name, buildinfo = ext
            else:
                name = ext.name
            if name.endswith('module'):
                name = name[:-6]
            yield name

    def handle_display_options(self, option_or
        """If there were any non-global "displ
        (--help-commands or the metadata displ
        line, display the requested info and r
        false.
        """
        import sys

        if self.help_commands:
            return _Distribution.handle_displa

        # Stdout may be StringIO (e.g. in test
        if not isinstance(sys.stdout, io.TextI
            return _Distribution.handle_displa

        # Don't wrap stdout if utf-8 is alread
        #  workaround for #334.
        if sys.stdout.encoding.lower() in ('ut
            return _Distribution.handle_displa

        # Print metadata in UTF-8 no matter th
        encoding = sys.stdout.encoding
        errors = sys.stdout.errors
        newline = sys.platform != 'win32' and 
        line_buffering = sys.stdout.line_buffe

        sys.stdout = io.TextIOWrapper(
            sys.stdout.detach(), 'utf-8', erro
        )
        try:
            return _Distribution.handle_displa
        finally:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.detach(), encoding,
            )


class DistDeprecationWarning(SetuptoolsDepreca
    """Class for warning about deprecations in
    setuptools. Not ignored by default, unlike
