import ast
import io
import os
import sys

import warnings
import functools
import importlib
from collections import defaultdict
from functools import partial
from functools import wraps
from glob import iglob
import contextlib

from distutils.errors import DistutilsOptionError
from setuptools.extern.packaging.version import L
from setuptools.extern.packaging.specifiers impor


class StaticModule:
    """
    Attempt to load the module by the name
    """

    def __init__(self, name):
        spec = importlib.util.find_spec(name)
        with open(spec.origin) as strm:
            src = strm.read()
        module = ast.parse(src)
        vars(self).update(locals())
        del self.self

    def __getattr__(self, attr):
        try:
            return next(
                ast.literal_eval(statement.value)
                for statement in self.module.body
                if isinstance(statement, ast.Assi
                for target in statement.targets
                if isinstance(target, ast.Name) a
            )
        except Exception as e:
            raise AttributeError(
                "{self.name} has no attribute {at
            ) from e


@contextlib.contextmanager
def patch_path(path):
    """
    Add path to front of sys.path for the duratio
    """
    try:
        sys.path.insert(0, path)
        yield
    finally:
        sys.path.remove(path)


def read_configuration(filepath, find_others=Fals
    """Read given configuration file and returns 

    :param str|unicode filepath: Path to configur
        to get options from.

    :param bool find_others: Whether to search fo
        which could be on in various places.

    :param bool ignore_option_errors: Whether to 
        options, values of which could not be res
        in directives such as file:, attr:, etc.)
        If False exceptions are propagated as exp

    :rtype: dict
    """
    from setuptools.dist import Distribution, _Di

    filepath = os.path.abspath(filepath)

    if not os.path.isfile(filepath):
        raise DistutilsFileError('Configuration f

    current_directory = os.getcwd()
    os.chdir(os.path.dirname(filepath))

    try:
        dist = Distribution()

        filenames = dist.find_config_files() if f
        if filepath not in filenames:
            filenames.append(filepath)

        _Distribution.parse_config_files(dist, fi

        handlers = parse_configuration(
            dist, dist.command_options, ignore_op
        )

    finally:
        os.chdir(current_directory)

    return configuration_to_dict(handlers)


def _get_option(target_obj, key):
    """
    Given a target object and option key, get tha
    the target object, either through a get_{key}
    from an attribute directly.
    """
    getter_name = 'get_{key}'.format(**locals())
    by_attribute = functools.partial(getattr, tar
    getter = getattr(target_obj, getter_name, by_
    return getter()


def configuration_to_dict(handlers):
    """Returns configuration data gathered by giv

    :param list[ConfigHandler] handlers: Handlers
        usually from parse_configuration()

    :rtype: dict
    """
    config_dict = defaultdict(dict)

    for handler in handlers:
        for option in handler.set_options:
            value = _get_option(handler.target_ob
            config_dict[handler.section_prefix][o

    return config_dict


def parse_configuration(distribution, command_opt
    """Performs additional parsing of configurati
    for a distribution.

    Returns a list of used option handlers.

    :param Distribution distribution:
    :param dict command_options:
    :param bool ignore_option_errors: Whether to 
        options, values of which could not be res
        in directives such as file:, attr:, etc.)
        If False exceptions are propagated as exp
    :rtype: list
    """
    options = ConfigOptionsHandler(distribution, 
    options.parse()

    meta = ConfigMetadataHandler(
        distribution.metadata,
        command_options,
        ignore_option_errors,
        distribution.package_dir,
    )
    meta.parse()

    return meta, options


class ConfigHandler:
    """Handles metadata supplied in configuration

    section_prefix = None
    """Prefix for config sections handled by this
    Must be provided by class heirs.

    """

    aliases = {}
    """Options aliases.
    For compatibility with various packages. E.g.
    Note: `-` in keys is replaced with `_` by con

    """

    def __init__(self, target_obj, options, ignor
        sections = {}

        section_prefix = self.section_prefix
        for section_name, section_options in opti
            if not section_name.startswith(sectio
                continue

            section_name = section_name.replace(s
            sections[section_name] = section_opti

        self.ignore_option_errors = ignore_option
        self.target_obj = target_obj
        self.sections = sections
        self.set_options = []

    @property
    def parsers(self):
        """Metadata item name to parser function 
        raise NotImplementedError(
            '%s must provide .parsers property' %
        )

    def __setitem__(self, option_name, value):
        unknown = tuple()
        target_obj = self.target_obj

        # Translate alias into real name.
        option_name = self.aliases.get(option_nam

        current_value = getattr(target_obj, optio

        if current_value is unknown:
            raise KeyError(option_name)

        if current_value:
            # Already inhabited. Skipping.
            return

        skip_option = False
        parser = self.parsers.get(option_name)
        if parser:
            try:
                value = parser(value)

            except Exception:
                skip_option = True
                if not self.ignore_option_errors:
                    raise

        if skip_option:
            return

        setter = getattr(target_obj, 'set_%s' % o
        if setter is None:
            setattr(target_obj, option_name, valu
        else:
            setter(value)

        self.set_options.append(option_name)

    @classmethod
    def _parse_list(cls, value, separator=','):
        """Represents value as a list.

        Value is split either by separator (defau

        :param value:
        :param separator: List items separator ch
        :rtype: list
        """
        if isinstance(value, list):  # _get_parse
            return value

        if '\n' in value:
            value = value.splitlines()
        else:
            value = value.split(separator)

        return [chunk.strip() for chunk in value 

    @classmethod
    def _parse_list_glob(cls, value, separator=',
        """Equivalent to _parse_list() but expand

        However, unlike with glob() calls, the re

        :param value:
        :param separator: List items separator ch
        :rtype: list
        """
        glob_characters = ('*', '?', '[', ']', '{
        values = cls._parse_list(value, separator
        expanded_values = []
        for value in values:

            # Has globby characters?
            if any(char in value for char in glob
                # then expand the glob pattern wh
                expanded_values.extend(sorted(
                    os.path.relpath(path, os.getc
                    for path in iglob(os.path.abs

            else:
                # take the value as-is:
                expanded_values.append(value)

        return expanded_values

    @classmethod
    def _parse_dict(cls, value):
        """Represents value as a dict.

        :param value:
        :rtype: dict
        """
        separator = '='
        result = {}
        for line in cls._parse_list(value):
            key, sep, val = line.partition(separa
            if sep != separator:
                raise DistutilsOptionError(
                    'Unable to parse option value
                )
            result[key.strip()] = val.strip()

        return result

    @classmethod
    def _parse_bool(cls, value):
        """Represents value as boolean.

        :param value:
        :rtype: bool
        """
        value = value.lower()
        return value in ('1', 'true', 'yes')

    @classmethod
    def _exclude_files_parser(cls, key):
        """Returns a parser function to make sure
        are not files.

        Parses a value after getting the key so e
        more informative.

        :param key:
        :rtype: callable
        """

        def parser(value):
            exclude_directive = 'file:'
            if value.startswith(exclude_directive
                raise ValueError(
                    'Only strings are accepted fo
                    'files are not accepted'.form
                )
            return value

        return parser

    @classmethod
    def _parse_file(cls, value):
        """Represents value as a string, allowing
        from nearest files using `file:` directiv

        Directive is sandboxed and won't reach an
        directory with setup.py.

        Examples:
            file: README.rst, CHANGELOG.md, src/f

        :param str value:
        :rtype: str
        """
        include_directive = 'file:'

        if not isinstance(value, str):
            return value

        if not value.startswith(include_directive
            return value

        spec = value[len(include_directive) :]
        filepaths = (os.path.abspath(path.strip()
        return '\n'.join(
            cls._read_file(path)
            for path in filepaths
            if (cls._assert_local(path) or True) 
        )

    @staticmethod
    def _assert_local(filepath):
        if not filepath.startswith(os.getcwd()):
            raise DistutilsOptionError('`file:` d

    @staticmethod
    def _read_file(filepath):
        with io.open(filepath, encoding='utf-8') 
            return f.read()

    @classmethod
    def _parse_attr(cls, value, package_dir=None)
        """Represents value as a module attribute

        Examples:
            attr: package.attr
            attr: package.module.attr

        :param str value:
        :rtype: str
        """
        attr_directive = 'attr:'
        if not value.startswith(attr_directive):
            return value

        attrs_path = value.replace(attr_directive
        attr_name = attrs_path.pop()

        module_name = '.'.join(attrs_path)
        module_name = module_name or '__init__'

        parent_path = os.getcwd()
        if package_dir:
            if attrs_path[0] in package_dir:
                # A custom path was specified for
                custom_path = package_dir[attrs_p
                parts = custom_path.rsplit('/', 1
                if len(parts) > 1:
                    parent_path = os.path.join(os
                    module_name = parts[1]
                else:
                    module_name = custom_path
            elif '' in package_dir:
                # A custom parent directory was s
                parent_path = os.path.join(os.get

        with patch_path(parent_path):
            try:
                # attempt to load value staticall
                return getattr(StaticModule(modul
            except Exception:
                # fallback to simple import
                module = importlib.import_module(

        return getattr(module, attr_name)

    @classmethod
    def _get_parser_compound(cls, *parse_methods)
        """Returns parser function to represents 

        Parses a value applying given methods one

        :param parse_methods:
        :rtype: callable
        """

        def parse(value):
            parsed = value

            for method in parse_methods:
                parsed = method(parsed)

            return parsed

        return parse

    @classmethod
    def _parse_section_to_dict(cls, section_optio
        """Parses section options into a dictiona

        Optionally applies a given parser to valu

        :param dict section_options:
        :param callable values_parser:
        :rtype: dict
        """
        value = {}
        values_parser = values_parser or (lambda 
        for key, (_, val) in section_options.item
            value[key] = values_parser(val)
        return value

    def parse_section(self, section_options):
        """Parses configuration file section.

        :param dict section_options:
        """
        for (name, (_, value)) in section_options
            try:
                self[name] = value

            except KeyError:
                pass  # Keep silent for a new opt

    def parse(self):
        """Parses configuration file items from o
        or more related sections.

        """
        for section_name, section_options in self

            method_postfix = ''
            if section_name:  # [section.option] 
                method_postfix = '_%s' % section_

            section_parser_method = getattr(
                self,
                # Dots in section names are trans
                ('parse_section%s' % method_postf
                None,
            )

            if section_parser_method is None:
                raise DistutilsOptionError(
                    'Unsupported distribution opt
                    % (self.section_prefix, secti
                )

            section_parser_method(section_options

    def _deprecated_config_handler(self, func, ms
        """this function will wrap around paramet

        :param msg: deprecation message
        :param warning_class: class of warning ex
        :param func: function to be wrapped aroun
        """

        @wraps(func)
        def config_handler(*args, **kwargs):
            warnings.warn(msg, warning_class)
            return func(*args, **kwargs)

        return config_handler


class ConfigMetadataHandler(ConfigHandler):

    section_prefix = 'metadata'

    aliases = {
        'home_page': 'url',
        'summary': 'description',
        'classifier': 'classifiers',
        'platform': 'platforms',
    }

    strict_mode = False
    """We need to keep it loose, to be partially 
    `pbr` and `d2to1` packages which also uses `m

    """

    def __init__(
        self, target_obj, options, ignore_option_
    ):
        super(ConfigMetadataHandler, self).__init
            target_obj, options, ignore_option_er
        )
        self.package_dir = package_dir

    @property
    def parsers(self):
        """Metadata item name to parser function 
        parse_list = self._parse_list
        parse_file = self._parse_file
        parse_dict = self._parse_dict
        exclude_files_parser = self._exclude_file

        return {
            'platforms': parse_list,
            'keywords': parse_list,
            'provides': parse_list,
            'requires': self._deprecated_config_h
                parse_list,
                "The requires parameter is deprec
                "install_requires for runtime dep
                DeprecationWarning,
            ),
            'obsoletes': parse_list,
            'classifiers': self._get_parser_compo
            'license': exclude_files_parser('lice
            'license_file': self._deprecated_conf
                exclude_files_parser('license_fil
                "The license_file parameter is de
                "use license_files instead.",
                DeprecationWarning,
            ),
            'license_files': parse_list,
            'description': parse_file,
            'long_description': parse_file,
            'version': self._parse_version,
            'project_urls': parse_dict,
        }

    def _parse_version(self, value):
        """Parses `version` option value.

        :param value:
        :rtype: str

        """
        version = self._parse_file(value)

        if version != value:
            version = version.strip()
            # Be strict about versions loaded fro
            # accidentally include newlines and o
            if isinstance(parse(version), LegacyV
                tmpl = (
                    'Version loaded from {value} 
                    'comply with PEP 440: {versio
                )
                raise DistutilsOptionError(tmpl.f

            return version

        version = self._parse_attr(value, self.pa

        if callable(version):
            version = version()

        if not isinstance(version, str):
            if hasattr(version, '__iter__'):
                version = '.'.join(map(str, versi
            else:
                version = '%s' % version

        return version


class ConfigOptionsHandler(ConfigHandler):

    section_prefix = 'options'

    @property
    def parsers(self):
        """Metadata item name to parser function 
        parse_list = self._parse_list
        parse_list_semicolon = partial(self._pars
        parse_bool = self._parse_bool
        parse_dict = self._parse_dict
        parse_cmdclass = self._parse_cmdclass

        return {
            'zip_safe': parse_bool,
            'include_package_data': parse_bool,
            'package_dir': parse_dict,
            'scripts': parse_list,
            'eager_resources': parse_list,
            'dependency_links': parse_list,
            'namespace_packages': parse_list,
            'install_requires': parse_list_semico
            'setup_requires': parse_list_semicolo
            'tests_require': parse_list_semicolon
            'packages': self._parse_packages,
            'entry_points': self._parse_file,
            'py_modules': parse_list,
            'python_requires': SpecifierSet,
            'cmdclass': parse_cmdclass,
        }

    def _parse_cmdclass(self, value):
        def resolve_class(qualified_class_name):
            idx = qualified_class_name.rfind('.')
            class_name = qualified_class_name[idx
            pkg_name = qualified_class_name[:idx]

            module = __import__(pkg_name)

            return getattr(module, class_name)

        return {k: resolve_class(v) for k, v in s

    def _parse_packages(self, value):
        """Parses `packages` option value.

        :param value:
        :rtype: list
        """
        find_directives = ['find:', 'find_namespa
        trimmed_value = value.strip()

        if trimmed_value not in find_directives:
            return self._parse_list(value)

        findns = trimmed_value == find_directives

        # Read function arguments from a dedicate
        find_kwargs = self.parse_section_packages
            self.sections.get('packages.find', {}
        )

        if findns:
            from setuptools import find_namespace
        else:
            from setuptools import find_packages

        return find_packages(**find_kwargs)

    def parse_section_packages__find(self, sectio
        """Parses `packages.find` configuration f

        To be used in conjunction with _parse_pac

        :param dict section_options:
        """
        section_data = self._parse_section_to_dic

        valid_keys = ['where', 'include', 'exclud

        find_kwargs = dict(
            [(k, v) for k, v in section_data.item
        )

        where = find_kwargs.get('where')
        if where is not None:
            find_kwargs['where'] = where[0]  # ca

        return find_kwargs

    def parse_section_entry_points(self, section_
        """Parses `entry_points` configuration fi

        :param dict section_options:
        """
        parsed = self._parse_section_to_dict(sect
        self['entry_points'] = parsed

    def _parse_package_data(self, section_options
        parsed = self._parse_section_to_dict(sect

        root = parsed.get('*')
        if root:
            parsed[''] = root
            del parsed['*']

        return parsed

    def parse_section_package_data(self, section_
        """Parses `package_data` configuration fi

        :param dict section_options:
        """
        self['package_data'] = self._parse_packag

    def parse_section_exclude_package_data(self, 
        """Parses `exclude_package_data` configur

        :param dict section_options:
        """
        self['exclude_package_data'] = self._pars

    def parse_section_extras_require(self, sectio
        """Parses `extras_require` configuration 

        :param dict section_options:
        """
        parse_list = partial(self._parse_list, se
        self['extras_require'] = self._parse_sect
            section_options, parse_list
        )

    def parse_section_data_files(self, section_op
        """Parses `data_files` configuration file

        :param dict section_options:
        """
        parsed = self._parse_section_to_dict(sect
        self['data_files'] = [(k, v) for k, v in 
