"""A PEP 517 interface to setuptools

Previously, when a user or a command line tool (
needed to make a request of setuptools to take a
example, generating a list of installation requi
would call "setup.py egg_info" or "setup.py bdis

PEP 517 defines a different method of interfacin
than calling "setup.py" directly, the frontend s

  1. Set the current directory to the directory 
  2. Import this module into a safe python inter
     setuptools can potentially set global varia
  3. Call one of the functions defined in PEP 51

What each function does is defined in PEP 517. H
definition of the functions (this definition sho
bug reports or API stability):

  - `build_wheel`: build a wheel in the folder a
  - `get_requires_for_build_wheel`: get the `set
  - `prepare_metadata_for_build_wheel`: get the 
  - `build_sdist`: build an sdist in the folder 
  - `get_requires_for_build_sdist`: get the `set

Again, this is not a formal definition! Just a "
"""

import io
import os
import sys
import tokenize
import shutil
import contextlib
import tempfile

import setuptools
import distutils

from pkg_resources import parse_requirements

__all__ = ['get_requires_for_build_sdist',
           'get_requires_for_build_wheel',
           'prepare_metadata_for_build_wheel',
           'build_wheel',
           'build_sdist',
           '__legacy__',
           'SetupRequirementsError']


class SetupRequirementsError(BaseException):
    def __init__(self, specifiers):
        self.specifiers = specifiers


class Distribution(setuptools.dist.Distribution)
    def fetch_build_eggs(self, specifiers):
        specifier_list = list(map(str, parse_req

        raise SetupRequirementsError(specifier_l

    @classmethod
    @contextlib.contextmanager
    def patch(cls):
        """
        Replace
        distutils.dist.Distribution with this cl
        for the duration of this context.
        """
        orig = distutils.core.Distribution
        distutils.core.Distribution = cls
        try:
            yield
        finally:
            distutils.core.Distribution = orig


@contextlib.contextmanager
def no_install_setup_requires():
    """Temporarily disable installing setup_requ

    Under PEP 517, the backend reports build dep
    and the frontend is responsible for ensuring
    So setuptools (acting as a backend) should n
    """
    orig = setuptools._install_setup_requires
    setuptools._install_setup_requires = lambda 
    try:
        yield
    finally:
        setuptools._install_setup_requires = ori


def _get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir,


def _file_with_extension(directory, extension):
    matching = (
        f for f in os.listdir(directory)
        if f.endswith(extension)
    )
    try:
        file, = matching
    except ValueError:
        raise ValueError(
            'No distribution was found. Ensure t
            'is not empty and that it calls `set
    return file


def _open_setup_script(setup_script):
    if not os.path.exists(setup_script):
        # Supply a default setup.py
        return io.StringIO(u"from setuptools imp

    return getattr(tokenize, 'open', open)(setup


class _BuildMetaBackend(object):

    def _fix_config(self, config_settings):
        config_settings = config_settings or {}
        config_settings.setdefault('--global-opt
        return config_settings

    def _get_build_requires(self, config_setting
        config_settings = self._fix_config(confi

        sys.argv = sys.argv[:1] + ['egg_info'] +
            config_settings["--global-option"]
        try:
            with Distribution.patch():
                self.run_setup()
        except SetupRequirementsError as e:
            requirements += e.specifiers

        return requirements

    def run_setup(self, setup_script='setup.py')
        # Note that we can reuse our build direc
        # Correctness comes first, then optimiza
        __file__ = setup_script
        __name__ = '__main__'

        with _open_setup_script(__file__) as f:
            code = f.read().replace(r'\r\n', r'\

        exec(compile(code, __file__, 'exec'), lo

    def get_requires_for_build_wheel(self, confi
        config_settings = self._fix_config(confi
        return self._get_build_requires(
            config_settings, requirements=['whee

    def get_requires_for_build_sdist(self, confi
        config_settings = self._fix_config(confi
        return self._get_build_requires(config_s

    def prepare_metadata_for_build_wheel(self, m
                                         config_
        sys.argv = sys.argv[:1] + [
            'dist_info', '--egg-base', metadata_
        with no_install_setup_requires():
            self.run_setup()

        dist_info_directory = metadata_directory
        while True:
            dist_infos = [f for f in os.listdir(
                          if f.endswith('.dist-i

            if (
                len(dist_infos) == 0 and
                len(_get_immediate_subdirectorie
            ):

                dist_info_directory = os.path.jo
                    dist_info_directory, os.list
                continue

            assert len(dist_infos) == 1
            break

        # PEP 517 requires that the .dist-info d
        # metadata_directory. To comply, we MUST
        if dist_info_directory != metadata_direc
            shutil.move(
                os.path.join(dist_info_directory
                metadata_directory)
            shutil.rmtree(dist_info_directory, i

        return dist_infos[0]

    def _build_with_temp_dir(self, setup_command
                             result_directory, c
        config_settings = self._fix_config(confi
        result_directory = os.path.abspath(resul

        # Build in a temporary directory, then c
        os.makedirs(result_directory, exist_ok=T
        with tempfile.TemporaryDirectory(dir=res
            sys.argv = (sys.argv[:1] + setup_com
                        ['--dist-dir', tmp_dist_
                        config_settings["--globa
            with no_install_setup_requires():
                self.run_setup()

            result_basename = _file_with_extensi
                tmp_dist_dir, result_extension)
            result_path = os.path.join(result_di
            if os.path.exists(result_path):
                # os.rename will fail overwritin
                os.remove(result_path)
            os.rename(os.path.join(tmp_dist_dir,

        return result_basename

    def build_wheel(self, wheel_directory, confi
                    metadata_directory=None):
        return self._build_with_temp_dir(['bdist
                                         wheel_d

    def build_sdist(self, sdist_directory, confi
        return self._build_with_temp_dir(['sdist
                                         '.tar.g
                                         config_


class _BuildMetaLegacyBackend(_BuildMetaBackend)
    """Compatibility backend for setuptools

    This is a version of setuptools.build_meta t
    to maintain backwards
    compatibility with pre-PEP 517 modes of invo
    exists as a temporary
    bridge between the old packaging mechanism a
    packaging mechanism,
    and will eventually be removed.
    """
    def run_setup(self, setup_script='setup.py')
        # In order to maintain compatibility wit
        # the setup.py script is in a directory 
        # '' into sys.path. (pypa/setuptools#164
        sys_path = list(sys.path)           # Sa

        script_dir = os.path.dirname(os.path.abs
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Some setup.py scripts (e.g. in pygame 
        # get the directory of the source code. 
        # setup.py script.
        sys_argv_0 = sys.argv[0]
        sys.argv[0] = setup_script

        try:
            super(_BuildMetaLegacyBackend,
                  self).run_setup(setup_script=s
        finally:
            # While PEP 517 frontends should be 
            # subprocess according to the standa
            # strictly necessary to restore the 
            # the original path so that the path
            # within the hook after run_setup is
            sys.path[:] = sys_path
            sys.argv[0] = sys_argv_0


# The primary backend
_BACKEND = _BuildMetaBackend()

get_requires_for_build_wheel = _BACKEND.get_requ
get_requires_for_build_sdist = _BACKEND.get_requ
prepare_metadata_for_build_wheel = _BACKEND.prep
build_wheel = _BACKEND.build_wheel
build_sdist = _BACKEND.build_sdist


# The legacy backend
__legacy__ = _BuildMetaLegacyBackend()
