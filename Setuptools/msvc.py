"""
Improved support for Microsoft Visual C++ compil

Known supported compilers:
--------------------------
Microsoft Visual C++ 9.0:
    Microsoft Visual C++ Compiler for Python 2.7
    Microsoft Windows SDK 6.1 (x86, x64, ia64)
    Microsoft Windows SDK 7.0 (x86, x64, ia64)

Microsoft Visual C++ 10.0:
    Microsoft Windows SDK 7.1 (x86, x64, ia64)

Microsoft Visual C++ 14.X:
    Microsoft Visual C++ Build Tools 2015 (x86, 
    Microsoft Visual Studio Build Tools 2017 (x8
    Microsoft Visual Studio Build Tools 2019 (x8

This may also support compilers shipped with com
"""

import json
from io import open
from os import listdir, pathsep
from os.path import join, isfile, isdir, dirname
import sys
import contextlib
import platform
import itertools
import subprocess
import distutils.errors
from setuptools.extern.packaging.version import 
from setuptools.extern.more_itertools import uni

from .monkey import get_unpatched

if platform.system() == 'Windows':
    import winreg
    from os import environ
else:
    # Mock winreg and environ so the module can 

    class winreg:
        HKEY_USERS = None
        HKEY_CURRENT_USER = None
        HKEY_LOCAL_MACHINE = None
        HKEY_CLASSES_ROOT = None

    environ = dict()

_msvc9_suppress_errors = (
    # msvc9compiler isn't available on some plat
    ImportError,

    # msvc9compiler raises DistutilsPlatformErro
    # environments. See #1118.
    distutils.errors.DistutilsPlatformError,
)

try:
    from distutils.msvc9compiler import Reg
except _msvc9_suppress_errors:
    pass


def msvc9_find_vcvarsall(version):
    """
    Patched "distutils.msvc9compiler.find_vcvars
    compiler build for Python
    (VCForPython / Microsoft Visual C++ Compiler

    Fall back to original behavior when the stan
    available.

    Redirect the path of "vcvarsall.bat".

    Parameters
    ----------
    version: float
        Required Microsoft Visual C++ version.

    Return
    ------
    str
        vcvarsall.bat path
    """
    vc_base = r'Software\%sMicrosoft\DevDiv\VCFo
    key = vc_base % ('', version)
    try:
        # Per-user installs register the compile
        productdir = Reg.get_value(key, "install
    except KeyError:
        try:
            # All-user installs on a 64-bit syst
            key = vc_base % ('Wow6432Node\\', ve
            productdir = Reg.get_value(key, "ins
        except KeyError:
            productdir = None

    if productdir:
        vcvarsall = join(productdir, "vcvarsall.
        if isfile(vcvarsall):
            return vcvarsall

    return get_unpatched(msvc9_find_vcvarsall)(v


def msvc9_query_vcvarsall(ver, arch='x86', *args
    """
    Patched "distutils.msvc9compiler.query_vcvar
    Microsoft Visual C++ 9.0 and 10.0 compilers.

    Set environment without use of "vcvarsall.ba

    Parameters
    ----------
    ver: float
        Required Microsoft Visual C++ version.
    arch: str
        Target architecture.

    Return
    ------
    dict
        environment
    """
    # Try to get environment from vcvarsall.bat 
    try:
        orig = get_unpatched(msvc9_query_vcvarsa
        return orig(ver, arch, *args, **kwargs)
    except distutils.errors.DistutilsPlatformErr
        # Pass error if Vcvarsall.bat is missing
        pass
    except ValueError:
        # Pass error if environment not set afte
        pass

    # If error, try to set environment directly
    try:
        return EnvironmentInfo(arch, ver).return
    except distutils.errors.DistutilsPlatformErr
        _augment_exception(exc, ver, arch)
        raise


def _msvc14_find_vc2015():
    """Python 3.8 "distutils/_msvccompiler.py" b
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\VisualStudio\Sx
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_3
        )
    except OSError:
        return None, None

    best_version = 0
    best_dir = None
    with key:
        for i in itertools.count():
            try:
                v, vc_dir, vt = winreg.EnumValue
            except OSError:
                break
            if v and vt == winreg.REG_SZ and isd
                try:
                    version = int(float(v))
                except (ValueError, TypeError):
                    continue
                if version >= 14 and version > b
                    best_version, best_dir = ver
    return best_version, best_dir


def _msvc14_find_vc2017():
    """Python 3.8 "distutils/_msvccompiler.py" b

    Returns "15, path" based on the result of in
    If no install is found, returns "None, None"

    The version is returned to avoid unnecessari
    result. It may be ignored when the path is n

    If vswhere.exe is not available, by definiti
    installed.
    """
    root = environ.get("ProgramFiles(x86)") or e
    if not root:
        return None, None

    try:
        path = subprocess.check_output([
            join(root, "Microsoft Visual Studio"
            "-latest",
            "-prerelease",
            "-requiresAny",
            "-requires", "Microsoft.VisualStudio
            "-requires", "Microsoft.VisualStudio
            "-property", "installationPath",
            "-products", "*",
        ]).decode(encoding="mbcs", errors="stric
    except (subprocess.CalledProcessError, OSErr
        return None, None

    path = join(path, "VC", "Auxiliary", "Build"
    if isdir(path):
        return 15, path

    return None, None


PLAT_SPEC_TO_RUNTIME = {
    'x86': 'x86',
    'x86_amd64': 'x64',
    'x86_arm': 'arm',
    'x86_arm64': 'arm64'
}


def _msvc14_find_vcvarsall(plat_spec):
    """Python 3.8 "distutils/_msvccompiler.py" b
    _, best_dir = _msvc14_find_vc2017()
    vcruntime = None

    if plat_spec in PLAT_SPEC_TO_RUNTIME:
        vcruntime_plat = PLAT_SPEC_TO_RUNTIME[pl
    else:
        vcruntime_plat = 'x64' if 'amd64' in pla

    if best_dir:
        vcredist = join(best_dir, "..", "..", "r
                        vcruntime_plat, "Microso
                        "vcruntime140.dll")
        try:
            import glob
            vcruntime = glob.glob(vcredist, recu
        except (ImportError, OSError, LookupErro
            vcruntime = None

    if not best_dir:
        best_version, best_dir = _msvc14_find_vc
        if best_version:
            vcruntime = join(best_dir, 'redist',
                             "Microsoft.VC140.CR

    if not best_dir:
        return None, None

    vcvarsall = join(best_dir, "vcvarsall.bat")
    if not isfile(vcvarsall):
        return None, None

    if not vcruntime or not isfile(vcruntime):
        vcruntime = None

    return vcvarsall, vcruntime


def _msvc14_get_vc_env(plat_spec):
    """Python 3.8 "distutils/_msvccompiler.py" b
    if "DISTUTILS_USE_SDK" in environ:
        return {
            key.lower(): value
            for key, value in environ.items()
        }

    vcvarsall, vcruntime = _msvc14_find_vcvarsal
    if not vcvarsall:
        raise distutils.errors.DistutilsPlatform
            "Unable to find vcvarsall.bat"
        )

    try:
        out = subprocess.check_output(
            'cmd /u /c "{}" {} && set'.format(vc
            stderr=subprocess.STDOUT,
        ).decode('utf-16le', errors='replace')
    except subprocess.CalledProcessError as exc:
        raise distutils.errors.DistutilsPlatform
            "Error executing {}".format(exc.cmd)
        ) from exc

    env = {
        key.lower(): value
        for key, _, value in
        (line.partition('=') for line in out.spl
        if key and value
    }

    if vcruntime:
        env['py_vcruntime_redist'] = vcruntime
    return env


def msvc14_get_vc_env(plat_spec):
    """
    Patched "distutils._msvccompiler._get_vc_env
    Microsoft Visual C++ 14.X compilers.

    Set environment without use of "vcvarsall.ba

    Parameters
    ----------
    plat_spec: str
        Target architecture.

    Return
    ------
    dict
        environment
    """

    # Always use backport from CPython 3.8
    try:
        return _msvc14_get_vc_env(plat_spec)
    except distutils.errors.DistutilsPlatformErr
        _augment_exception(exc, 14.0)
        raise


def msvc14_gen_lib_options(*args, **kwargs):
    """
    Patched "distutils._msvccompiler.gen_lib_opt
    compatibility between "numpy.distutils" and 
    (for Numpy < 1.11.2)
    """
    if "numpy.distutils" in sys.modules:
        import numpy as np
        if LegacyVersion(np.__version__) < Legac
            return np.distutils.ccompiler.gen_li
    return get_unpatched(msvc14_gen_lib_options)


def _augment_exception(exc, version, arch=''):
    """
    Add details to the exception message to help
    as to what action will resolve it.
    """
    # Error if MSVC++ directory not found or env
    message = exc.args[0]

    if "vcvarsall" in message.lower() or "visual
        # Special error message if MSVC++ not in
        tmpl = 'Microsoft Visual C++ {version:0.
        message = tmpl.format(**locals())
        msdownload = 'www.microsoft.com/download
        if version == 9.0:
            if arch.lower().find('ia64') > -1:
                # For VC++ 9.0, if IA64 support 
                # to Windows SDK 7.0.
                # Note: No download link availab
                message += ' Get it with "Micros
            else:
                # For VC++ 9.0 redirect user to 
                # This redirection link is maint
                # Contact vspython@microsoft.com
                message += ' Get it from http://
        elif version == 10.0:
            # For VC++ 10.0 Redirect user to Win
            message += ' Get it with "Microsoft 
            message += msdownload % 8279
        elif version >= 14.0:
            # For VC++ 14.X Redirect user to lat
            message += (' Get it with "Microsoft
                        r'https://visualstudio.m
                        r'/visual-cpp-build-tool

    exc.args = (message, )


class PlatformInfo:
    """
    Current and Target Architectures information

    Parameters
    ----------
    arch: str
        Target architecture.
    """
    current_cpu = environ.get('processor_archite

    def __init__(self, arch):
        self.arch = arch.lower().replace('x64', 

    @property
    def target_cpu(self):
        """
        Return Target CPU architecture.

        Return
        ------
        str
            Target CPU
        """
        return self.arch[self.arch.find('_') + 1

    def target_is_x86(self):
        """
        Return True if target CPU is x86 32 bits

        Return
        ------
        bool
            CPU is x86 32 bits
        """
        return self.target_cpu == 'x86'

    def current_is_x86(self):
        """
        Return True if current CPU is x86 32 bit

        Return
        ------
        bool
            CPU is x86 32 bits
        """
        return self.current_cpu == 'x86'

    def current_dir(self, hidex86=False, x64=Fal
        """
        Current platform specific subfolder.

        Parameters
        ----------
        hidex86: bool
            return '' and not '\x86' if architec
        x64: bool
            return '\x64' and not '\amd64' if ar

        Return
        ------
        str
            subfolder: '\target', or '' (see hid
        """
        return (
            '' if (self.current_cpu == 'x86' and
            r'\x64' if (self.current_cpu == 'amd
            r'\%s' % self.current_cpu
        )

    def target_dir(self, hidex86=False, x64=Fals
        r"""
        Target platform specific subfolder.

        Parameters
        ----------
        hidex86: bool
            return '' and not '\x86' if architec
        x64: bool
            return '\x64' and not '\amd64' if ar

        Return
        ------
        str
            subfolder: '\current', or '' (see hi
        """
        return (
            '' if (self.target_cpu == 'x86' and 
            r'\x64' if (self.target_cpu == 'amd6
            r'\%s' % self.target_cpu
        )

    def cross_dir(self, forcex86=False):
        r"""
        Cross platform specific subfolder.

        Parameters
        ----------
        forcex86: bool
            Use 'x86' as current architecture ev
            not x86.

        Return
        ------
        str
            subfolder: '' if target architecture
            '\current_target' if not.
        """
        current = 'x86' if forcex86 else self.cu
        return (
            '' if self.target_cpu == current els
            self.target_dir().replace('\\', '\\%
        )


class RegistryInfo:
    """
    Microsoft Visual Studio related registry inf

    Parameters
    ----------
    platform_info: PlatformInfo
        "PlatformInfo" instance.
    """
    HKEYS = (winreg.HKEY_USERS,
             winreg.HKEY_CURRENT_USER,
             winreg.HKEY_LOCAL_MACHINE,
             winreg.HKEY_CLASSES_ROOT)

    def __init__(self, platform_info):
        self.pi = platform_info

    @property
    def visualstudio(self):
        """
        Microsoft Visual Studio root registry ke

        Return
        ------
        str
            Registry key
        """
        return 'VisualStudio'

    @property
    def sxs(self):
        """
        Microsoft Visual Studio SxS registry key

        Return
        ------
        str
            Registry key
        """
        return join(self.visualstudio, 'SxS')

    @property
    def vc(self):
        """
        Microsoft Visual C++ VC7 registry key.

        Return
        ------
        str
            Registry key
        """
        return join(self.sxs, 'VC7')

    @property
    def vs(self):
        """
        Microsoft Visual Studio VS7 registry key

        Return
        ------
        str
            Registry key
        """
        return join(self.sxs, 'VS7')

    @property
    def vc_for_python(self):
        """
        Microsoft Visual C++ for Python registry

        Return
        ------
        str
            Registry key
        """
        return r'DevDiv\VCForPython'

    @property
    def microsoft_sdk(self):
        """
        Microsoft SDK registry key.

        Return
        ------
        str
            Registry key
        """
        return 'Microsoft SDKs'

    @property
    def windows_sdk(self):
        """
        Microsoft Windows/Platform SDK registry 

        Return
        ------
        str
            Registry key
        """
        return join(self.microsoft_sdk, 'Windows

    @property
    def netfx_sdk(self):
        """
        Microsoft .NET Framework SDK registry ke

        Return
        ------
        str
            Registry key
        """
        return join(self.microsoft_sdk, 'NETFXSD

    @property
    def windows_kits_roots(self):
        """
        Microsoft Windows Kits Roots registry ke

        Return
        ------
        str
            Registry key
        """
        return r'Windows Kits\Installed Roots'

    def microsoft(self, key, x86=False):
        """
        Return key in Microsoft software registr

        Parameters
        ----------
        key: str
            Registry key path where look.
        x86: str
            Force x86 software registry.

        Return
        ------
        str
            Registry key
        """
        node64 = '' if self.pi.current_is_x86() 
        return join('Software', node64, 'Microso

    def lookup(self, key, name):
        """
        Look for values in registry in Microsoft

        Parameters
        ----------
        key: str
            Registry key path where look.
        name: str
            Value name to find.

        Return
        ------
        str
            value
        """
        key_read = winreg.KEY_READ
        openkey = winreg.OpenKey
        closekey = winreg.CloseKey
        ms = self.microsoft
        for hkey in self.HKEYS:
            bkey = None
            try:
                bkey = openkey(hkey, ms(key), 0,
            except (OSError, IOError):
                if not self.pi.current_is_x86():
                    try:
                        bkey = openkey(hkey, ms(
                    except (OSError, IOError):
                        continue
                else:
                    continue
            try:
                return winreg.QueryValueEx(bkey,
            except (OSError, IOError):
                pass
            finally:
                if bkey:
                    closekey(bkey)


class SystemInfo:
    """
    Microsoft Windows and Visual Studio related 

    Parameters
    ----------
    registry_info: RegistryInfo
        "RegistryInfo" instance.
    vc_ver: float
        Required Microsoft Visual C++ version.
    """

    # Variables and properties in this class use
    # names from Microsoft source files for more
    WinDir = environ.get('WinDir', '')
    ProgramFiles = environ.get('ProgramFiles', '
    ProgramFilesx86 = environ.get('ProgramFiles(

    def __init__(self, registry_info, vc_ver=Non
        self.ri = registry_info
        self.pi = self.ri.pi

        self.known_vs_paths = self.find_programd

        # Except for VS15+, VC version is aligne
        self.vs_ver = self.vc_ver = (
            vc_ver or self._find_latest_availabl

    def _find_latest_available_vs_ver(self):
        """
        Find the latest VC version

        Return
        ------
        float
            version
        """
        reg_vc_vers = self.find_reg_vs_vers()

        if not (reg_vc_vers or self.known_vs_pat
            raise distutils.errors.DistutilsPlat
                'No Microsoft Visual C++ version

        vc_vers = set(reg_vc_vers)
        vc_vers.update(self.known_vs_paths)
        return sorted(vc_vers)[-1]

    def find_reg_vs_vers(self):
        """
        Find Microsoft Visual Studio versions av

        Return
        ------
        list of float
            Versions
        """
        ms = self.ri.microsoft
        vckeys = (self.ri.vc, self.ri.vc_for_pyt
        vs_vers = []
        for hkey, key in itertools.product(self.
            try:
                bkey = winreg.OpenKey(hkey, ms(k
            except (OSError, IOError):
                continue
            with bkey:
                subkeys, values, _ = winreg.Quer
                for i in range(values):
                    with contextlib.suppress(Val
                        ver = float(winreg.EnumV
                        if ver not in vs_vers:
                            vs_vers.append(ver)
                for i in range(subkeys):
                    with contextlib.suppress(Val
                        ver = float(winreg.EnumK
                        if ver not in vs_vers:
                            vs_vers.append(ver)
        return sorted(vs_vers)

    def find_programdata_vs_vers(self):
        r"""
        Find Visual studio 2017+ versions from i
        "C:\ProgramData\Microsoft\VisualStudio\P

        Return
        ------
        dict
            float version as key, path as value.
        """
        vs_versions = {}
        instances_dir = \
            r'C:\ProgramData\Microsoft\VisualStu

        try:
            hashed_names = listdir(instances_dir

        except (OSError, IOError):
            # Directory not exists with all Visu
            return vs_versions

        for name in hashed_names:
            try:
                # Get VS installation path from 
                state_path = join(instances_dir,
                with open(state_path, 'rt', enco
                    state = json.load(state_file
                vs_path = state['installationPat

                # Raises OSError if this VS inst
                listdir(join(vs_path, r'VC\Tools

                # Store version and path
                vs_versions[self._as_float_versi
                    state['installationVersion']

            except (OSError, IOError, KeyError):
                # Skip if "state.json" file is m
                continue

        return vs_versions

    @staticmethod
    def _as_float_version(version):
        """
        Return a string version as a simplified 

        Parameters
        ----------
        version: str
            Version.

        Return
        ------
        float
            version
        """
        return float('.'.join(version.split('.')

    @property
    def VSInstallDir(self):
        """
        Microsoft Visual Studio directory.

        Return
        ------
        str
            path
        """
        # Default path
        default = join(self.ProgramFilesx86,
                       'Microsoft Visual Studio 

        # Try to get path from registry, if fail
        return self.ri.lookup(self.ri.vs, '%0.1f

    @property
    def VCInstallDir(self):
        """
        Microsoft Visual C++ directory.

        Return
        ------
        str
            path
        """
        path = self._guess_vc() or self._guess_v

        if not isdir(path):
            msg = 'Microsoft Visual C++ director
            raise distutils.errors.DistutilsPlat

        return path

    def _guess_vc(self):
        """
        Locate Visual C++ for VS2017+.

        Return
        ------
        str
            path
        """
        if self.vs_ver <= 14.0:
            return ''

        try:
            # First search in known VS paths
            vs_dir = self.known_vs_paths[self.vs
        except KeyError:
            # Else, search with path from regist
            vs_dir = self.VSInstallDir

        guess_vc = join(vs_dir, r'VC\Tools\MSVC'

        # Subdir with VC exact version as name
        try:
            # Update the VC version with real on
            vc_ver = listdir(guess_vc)[-1]
            self.vc_ver = self._as_float_version
            return join(guess_vc, vc_ver)
        except (OSError, IOError, IndexError):
            return ''

    def _guess_vc_legacy(self):
        """
        Locate Visual C++ for versions prior to 

        Return
        ------
        str
            path
        """
        default = join(self.ProgramFilesx86,
                       r'Microsoft Visual Studio

        # Try to get "VC++ for Python" path from
        reg_path = join(self.ri.vc_for_python, '
        python_vc = self.ri.lookup(reg_path, 'in
        default_vc = join(python_vc, 'VC') if py

        # Try to get path from registry, if fail
        return self.ri.lookup(self.ri.vc, '%0.1f

    @property
    def WindowsSdkVersion(self):
        """
        Microsoft Windows SDK versions for speci

        Return
        ------
        tuple of str
            versions
        """
        if self.vs_ver <= 9.0:
            return '7.0', '6.1', '6.0a'
        elif self.vs_ver == 10.0:
            return '7.1', '7.0a'
        elif self.vs_ver == 11.0:
            return '8.0', '8.0a'
        elif self.vs_ver == 12.0:
            return '8.1', '8.1a'
        elif self.vs_ver >= 14.0:
            return '10.0', '8.1'

    @property
    def WindowsSdkLastVersion(self):
        """
        Microsoft Windows SDK last version.

        Return
        ------
        str
            version
        """
        return self._use_last_dir_name(join(self

    @property  # noqa: C901
    def WindowsSdkDir(self):  # noqa: C901  # is
        """
        Microsoft Windows SDK directory.

        Return
        ------
        str
            path
        """
        sdkdir = ''
        for ver in self.WindowsSdkVersion:
            # Try to get it from registry
            loc = join(self.ri.windows_sdk, 'v%s
            sdkdir = self.ri.lookup(loc, 'instal
            if sdkdir:
                break
        if not sdkdir or not isdir(sdkdir):
            # Try to get "VC++ for Python" versi
            path = join(self.ri.vc_for_python, '
            install_base = self.ri.lookup(path, 
            if install_base:
                sdkdir = join(install_base, 'Win
        if not sdkdir or not isdir(sdkdir):
            # If fail, use default new path
            for ver in self.WindowsSdkVersion:
                intver = ver[:ver.rfind('.')]
                path = r'Microsoft SDKs\Windows 
                d = join(self.ProgramFiles, path
                if isdir(d):
                    sdkdir = d
        if not sdkdir or not isdir(sdkdir):
            # If fail, use default old path
            for ver in self.WindowsSdkVersion:
                path = r'Microsoft SDKs\Windows\
                d = join(self.ProgramFiles, path
                if isdir(d):
                    sdkdir = d
        if not sdkdir:
            # If fail, use Platform SDK
            sdkdir = join(self.VCInstallDir, 'Pl
        return sdkdir

    @property
    def WindowsSDKExecutablePath(self):
        """
        Microsoft Windows SDK executable directo

        Return
        ------
        str
            path
        """
        # Find WinSDK NetFx Tools registry dir n
        if self.vs_ver <= 11.0:
            netfxver = 35
            arch = ''
        else:
            netfxver = 40
            hidex86 = True if self.vs_ver <= 12.
            arch = self.pi.current_dir(x64=True,
        fx = 'WinSDK-NetFx%dTools%s' % (netfxver

        # list all possibles registry paths
        regpaths = []
        if self.vs_ver >= 14.0:
            for ver in self.NetFxSdkVersion:
                regpaths += [join(self.ri.netfx_

        for ver in self.WindowsSdkVersion:
            regpaths += [join(self.ri.windows_sd

        # Return installation folder from the mo
        for path in regpaths:
            execpath = self.ri.lookup(path, 'ins
            if execpath:
                return execpath

    @property
    def FSharpInstallDir(self):
        """
        Microsoft Visual F# directory.

        Return
        ------
        str
            path
        """
        path = join(self.ri.visualstudio, r'%0.1
        return self.ri.lookup(path, 'productdir'

    @property
    def UniversalCRTSdkDir(self):
        """
        Microsoft Universal CRT SDK directory.

        Return
        ------
        str
            path
        """
        # Set Kit Roots versions for specified M
        vers = ('10', '81') if self.vs_ver >= 14

        # Find path of the more recent Kit
        for ver in vers:
            sdkdir = self.ri.lookup(self.ri.wind
                                    'kitsroot%s'
            if sdkdir:
                return sdkdir or ''

    @property
    def UniversalCRTSdkLastVersion(self):
        """
        Microsoft Universal C Runtime SDK last v

        Return
        ------
        str
            version
        """
        return self._use_last_dir_name(join(self

    @property
    def NetFxSdkVersion(self):
        """
        Microsoft .NET Framework SDK versions.

        Return
        ------
        tuple of str
            versions
        """
        # Set FxSdk versions for specified VS ve
        return (('4.7.2', '4.7.1', '4.7',
                 '4.6.2', '4.6.1', '4.6',
                 '4.5.2', '4.5.1', '4.5')
                if self.vs_ver >= 14.0 else ())

    @property
    def NetFxSdkDir(self):
        """
        Microsoft .NET Framework SDK directory.

        Return
        ------
        str
            path
        """
        sdkdir = ''
        for ver in self.NetFxSdkVersion:
            loc = join(self.ri.netfx_sdk, ver)
            sdkdir = self.ri.lookup(loc, 'kitsin
            if sdkdir:
                break
        return sdkdir

    @property
    def FrameworkDir32(self):
        """
        Microsoft .NET Framework 32bit directory

        Return
        ------
        str
            path
        """
        # Default path
        guess_fw = join(self.WinDir, r'Microsoft

        # Try to get path from registry, if fail
        return self.ri.lookup(self.ri.vc, 'frame

    @property
    def FrameworkDir64(self):
        """
        Microsoft .NET Framework 64bit directory

        Return
        ------
        str
            path
        """
        # Default path
        guess_fw = join(self.WinDir, r'Microsoft

        # Try to get path from registry, if fail
        return self.ri.lookup(self.ri.vc, 'frame

    @property
    def FrameworkVersion32(self):
        """
        Microsoft .NET Framework 32bit versions.

        Return
        ------
        tuple of str
            versions
        """
        return self._find_dot_net_versions(32)

    @property
    def FrameworkVersion64(self):
        """
        Microsoft .NET Framework 64bit versions.

        Return
        ------
        tuple of str
            versions
        """
        return self._find_dot_net_versions(64)

    def _find_dot_net_versions(self, bits):
        """
        Find Microsoft .NET Framework versions.

        Parameters
        ----------
        bits: int
            Platform number of bits: 32 or 64.

        Return
        ------
        tuple of str
            versions
        """
        # Find actual .NET version in registry
        reg_ver = self.ri.lookup(self.ri.vc, 'fr
        dot_net_dir = getattr(self, 'FrameworkDi
        ver = reg_ver or self._use_last_dir_name

        # Set .NET versions for specified MSVC++
        if self.vs_ver >= 12.0:
            return ver, 'v4.0'
        elif self.vs_ver >= 10.0:
            return 'v4.0.30319' if ver.lower()[:
        elif self.vs_ver == 9.0:
            return 'v3.5', 'v2.0.50727'
        elif self.vs_ver == 8.0:
            return 'v3.0', 'v2.0.50727'

    @staticmethod
    def _use_last_dir_name(path, prefix=''):
        """
        Return name of the last dir in path or '

        Parameters
        ----------
        path: str
            Use dirs in this path
        prefix: str
            Use only dirs starting by this prefi

        Return
        ------
        str
            name
        """
        matching_dirs = (
            dir_name
            for dir_name in reversed(listdir(pat
            if isdir(join(path, dir_name)) and
            dir_name.startswith(prefix)
        )
        return next(matching_dirs, None) or ''


class EnvironmentInfo:
    """
    Return environment variables for specified M
    and platform : Lib, Include, Path and libpat

    This function is compatible with Microsoft V

    Script created by analysing Microsoft enviro
    "vcvars[...].bat", "SetEnv.Cmd", "vcbuildtoo

    Parameters
    ----------
    arch: str
        Target architecture.
    vc_ver: float
        Required Microsoft Visual C++ version. I
        version.
    vc_min_ver: float
        Minimum Microsoft Visual C++ version.
    """

    # Variables and properties in this class use
    # names from Microsoft source files for more

    def __init__(self, arch, vc_ver=None, vc_min
        self.pi = PlatformInfo(arch)
        self.ri = RegistryInfo(self.pi)
        self.si = SystemInfo(self.ri, vc_ver)

        if self.vc_ver < vc_min_ver:
            err = 'No suitable Microsoft Visual 
            raise distutils.errors.DistutilsPlat

    @property
    def vs_ver(self):
        """
        Microsoft Visual Studio.

        Return
        ------
        float
            version
        """
        return self.si.vs_ver

    @property
    def vc_ver(self):
        """
        Microsoft Visual C++ version.

        Return
        ------
        float
            version
        """
        return self.si.vc_ver

    @property
    def VSTools(self):
        """
        Microsoft Visual Studio Tools.

        Return
        ------
        list of str
            paths
        """
        paths = [r'Common7\IDE', r'Common7\Tools

        if self.vs_ver >= 14.0:
            arch_subdir = self.pi.current_dir(hi
            paths += [r'Common7\IDE\CommonExtens
            paths += [r'Team Tools\Performance T
            paths += [r'Team Tools\Performance T

        return [join(self.si.VSInstallDir, path)

    @property
    def VCIncludes(self):
        """
        Microsoft Visual C++ & Microsoft Foundat

        Return
        ------
        list of str
            paths
        """
        return [join(self.si.VCInstallDir, 'Incl
                join(self.si.VCInstallDir, r'ATL

    @property
    def VCLibraries(self):
        """
        Microsoft Visual C++ & Microsoft Foundat

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver >= 15.0:
            arch_subdir = self.pi.target_dir(x64
        else:
            arch_subdir = self.pi.target_dir(hid
        paths = ['Lib%s' % arch_subdir, r'ATLMFC

        if self.vs_ver >= 14.0:
            paths += [r'Lib\store%s' % arch_subd

        return [join(self.si.VCInstallDir, path)

    @property
    def VCStoreRefs(self):
        """
        Microsoft Visual C++ store references Li

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 14.0:
            return []
        return [join(self.si.VCInstallDir, r'Lib

    @property
    def VCTools(self):
        """
        Microsoft Visual C++ Tools.

        Return
        ------
        list of str
            paths
        """
        si = self.si
        tools = [join(si.VCInstallDir, 'VCPackag

        forcex86 = True if self.vs_ver <= 10.0 e
        arch_subdir = self.pi.cross_dir(forcex86
        if arch_subdir:
            tools += [join(si.VCInstallDir, 'Bin

        if self.vs_ver == 14.0:
            path = 'Bin%s' % self.pi.current_dir
            tools += [join(si.VCInstallDir, path

        elif self.vs_ver >= 15.0:
            host_dir = (r'bin\HostX86%s' if self
                        r'bin\HostX64%s')
            tools += [join(
                si.VCInstallDir, host_dir % self

            if self.pi.current_cpu != self.pi.ta
                tools += [join(
                    si.VCInstallDir, host_dir % 

        else:
            tools += [join(si.VCInstallDir, 'Bin

        return tools

    @property
    def OSLibraries(self):
        """
        Microsoft Windows SDK Libraries.

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver <= 10.0:
            arch_subdir = self.pi.target_dir(hid
            return [join(self.si.WindowsSdkDir, 

        else:
            arch_subdir = self.pi.target_dir(x64
            lib = join(self.si.WindowsSdkDir, 'l
            libver = self._sdk_subdir
            return [join(lib, '%sum%s' % (libver

    @property
    def OSIncludes(self):
        """
        Microsoft Windows SDK Include.

        Return
        ------
        list of str
            paths
        """
        include = join(self.si.WindowsSdkDir, 'i

        if self.vs_ver <= 10.0:
            return [include, join(include, 'gl')

        else:
            if self.vs_ver >= 14.0:
                sdkver = self._sdk_subdir
            else:
                sdkver = ''
            return [join(include, '%sshared' % s
                    join(include, '%sum' % sdkve
                    join(include, '%swinrt' % sd

    @property
    def OSLibpath(self):
        """
        Microsoft Windows SDK Libraries Paths.

        Return
        ------
        list of str
            paths
        """
        ref = join(self.si.WindowsSdkDir, 'Refer
        libpath = []

        if self.vs_ver <= 9.0:
            libpath += self.OSLibraries

        if self.vs_ver >= 11.0:
            libpath += [join(ref, r'CommonConfig

        if self.vs_ver >= 14.0:
            libpath += [
                ref,
                join(self.si.WindowsSdkDir, 'Uni
                join(
                    ref, 'Windows.Foundation.Uni
                join(ref, 'Windows.Foundation.Fo
                join(
                    ref, 'Windows.Networking.Con
                    '1.0.0.0'),
                join(
                    self.si.WindowsSdkDir, 'Exte
                    '%0.1f' % self.vs_ver, 'Refe
                    'neutral'),
            ]
        return libpath

    @property
    def SdkTools(self):
        """
        Microsoft Windows SDK Tools.

        Return
        ------
        list of str
            paths
        """
        return list(self._sdk_tools())

    def _sdk_tools(self):
        """
        Microsoft Windows SDK Tools paths genera

        Return
        ------
        generator of str
            paths
        """
        if self.vs_ver < 15.0:
            bin_dir = 'Bin' if self.vs_ver <= 11
            yield join(self.si.WindowsSdkDir, bi

        if not self.pi.current_is_x86():
            arch_subdir = self.pi.current_dir(x6
            path = 'Bin%s' % arch_subdir
            yield join(self.si.WindowsSdkDir, pa

        if self.vs_ver in (10.0, 11.0):
            if self.pi.target_is_x86():
                arch_subdir = ''
            else:
                arch_subdir = self.pi.current_di
            path = r'Bin\NETFX 4.0 Tools%s' % ar
            yield join(self.si.WindowsSdkDir, pa

        elif self.vs_ver >= 15.0:
            path = join(self.si.WindowsSdkDir, '
            arch_subdir = self.pi.current_dir(x6
            sdkver = self.si.WindowsSdkLastVersi
            yield join(path, '%s%s' % (sdkver, a

        if self.si.WindowsSDKExecutablePath:
            yield self.si.WindowsSDKExecutablePa

    @property
    def _sdk_subdir(self):
        """
        Microsoft Windows SDK version subdir.

        Return
        ------
        str
            subdir
        """
        ucrtver = self.si.WindowsSdkLastVersion
        return ('%s\\' % ucrtver) if ucrtver els

    @property
    def SdkSetup(self):
        """
        Microsoft Windows SDK Setup.

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver > 9.0:
            return []

        return [join(self.si.WindowsSdkDir, 'Set

    @property
    def FxTools(self):
        """
        Microsoft .NET Framework Tools.

        Return
        ------
        list of str
            paths
        """
        pi = self.pi
        si = self.si

        if self.vs_ver <= 10.0:
            include32 = True
            include64 = not pi.target_is_x86() a
        else:
            include32 = pi.target_is_x86() or pi
            include64 = pi.current_cpu == 'amd64

        tools = []
        if include32:
            tools += [join(si.FrameworkDir32, ve
                      for ver in si.FrameworkVer
        if include64:
            tools += [join(si.FrameworkDir64, ve
                      for ver in si.FrameworkVer
        return tools

    @property
    def NetFxSDKLibraries(self):
        """
        Microsoft .Net Framework SDK Libraries.

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 14.0 or not self.si.Net
            return []

        arch_subdir = self.pi.target_dir(x64=Tru
        return [join(self.si.NetFxSdkDir, r'lib\

    @property
    def NetFxSDKIncludes(self):
        """
        Microsoft .Net Framework SDK Includes.

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 14.0 or not self.si.Net
            return []

        return [join(self.si.NetFxSdkDir, r'incl

    @property
    def VsTDb(self):
        """
        Microsoft Visual Studio Team System Data

        Return
        ------
        list of str
            paths
        """
        return [join(self.si.VSInstallDir, r'VST

    @property
    def MSBuild(self):
        """
        Microsoft Build Engine.

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 12.0:
            return []
        elif self.vs_ver < 15.0:
            base_path = self.si.ProgramFilesx86
            arch_subdir = self.pi.current_dir(hi
        else:
            base_path = self.si.VSInstallDir
            arch_subdir = ''

        path = r'MSBuild\%0.1f\bin%s' % (self.vs
        build = [join(base_path, path)]

        if self.vs_ver >= 15.0:
            # Add Roslyn C# & Visual Basic Compi
            build += [join(base_path, path, 'Ros

        return build

    @property
    def HTMLHelpWorkshop(self):
        """
        Microsoft HTML Help Workshop.

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 11.0:
            return []

        return [join(self.si.ProgramFilesx86, 'H

    @property
    def UCRTLibraries(self):
        """
        Microsoft Universal C Runtime SDK Librar

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 14.0:
            return []

        arch_subdir = self.pi.target_dir(x64=Tru
        lib = join(self.si.UniversalCRTSdkDir, '
        ucrtver = self._ucrt_subdir
        return [join(lib, '%sucrt%s' % (ucrtver,

    @property
    def UCRTIncludes(self):
        """
        Microsoft Universal C Runtime SDK Includ

        Return
        ------
        list of str
            paths
        """
        if self.vs_ver < 14.0:
            return []

        include = join(self.si.UniversalCRTSdkDi
        return [join(include, '%sucrt' % self._u

    @property
    def _ucrt_subdir(self):
        """
        Microsoft Universal C Runtime SDK versio

        Return
        ------
        str
            subdir
        """
        ucrtver = self.si.UniversalCRTSdkLastVer
        return ('%s\\' % ucrtver) if ucrtver els

    @property
    def FSharp(self):
        """
        Microsoft Visual F#.

        Return
        ------
        list of str
            paths
        """
        if 11.0 > self.vs_ver > 12.0:
            return []

        return [self.si.FSharpInstallDir]

    @property
    def VCRuntimeRedist(self):
        """
        Microsoft Visual C++ runtime redistribut

        Return
        ------
        str
            path
        """
        vcruntime = 'vcruntime%d0.dll' % self.vc
        arch_subdir = self.pi.target_dir(x64=Tru

        # Installation prefixes candidates
        prefixes = []
        tools_path = self.si.VCInstallDir
        redist_path = dirname(tools_path.replace
        if isdir(redist_path):
            # Redist version may not be exactly 
            redist_path = join(redist_path, list
            prefixes += [redist_path, join(redis

        prefixes += [join(tools_path, 'redist')]

        # CRT directory
        crt_dirs = ('Microsoft.VC%d.CRT' % (self
                    # Sometime store in director
                    'Microsoft.VC%d.CRT' % (int(

        # vcruntime path
        for prefix, crt_dir in itertools.product
            path = join(prefix, arch_subdir, crt
            if isfile(path):
                return path

    def return_env(self, exists=True):
        """
        Return environment dict.

        Parameters
        ----------
        exists: bool
            It True, only return existing paths.

        Return
        ------
        dict
            environment
        """
        env = dict(
            include=self._build_paths('include',
                                      [self.VCIn
                                       self.OSIn
                                       self.UCRT
                                       self.NetF
                                      exists),
            lib=self._build_paths('lib',
                                  [self.VCLibrar
                                   self.OSLibrar
                                   self.FxTools,
                                   self.UCRTLibr
                                   self.NetFxSDK
                                  exists),
            libpath=self._build_paths('libpath',
                                      [self.VCLi
                                       self.FxTo
                                       self.VCSt
                                       self.OSLi
                                      exists),
            path=self._build_paths('path',
                                   [self.VCTools
                                    self.VSTools
                                    self.VsTDb,
                                    self.SdkTool
                                    self.SdkSetu
                                    self.FxTools
                                    self.MSBuild
                                    self.HTMLHel
                                    self.FSharp]
                                   exists),
        )
        if self.vs_ver >= 14 and isfile(self.VCR
            env['py_vcruntime_redist'] = self.VC
        return env

    def _build_paths(self, name, spec_path_lists
        """
        Given an environment variable name and s
        return a pathsep-separated string of pat
        unique, extant, directories from those p
        the environment variable. Raise an error
        are resolved.

        Parameters
        ----------
        name: str
            Environment variable name
        spec_path_lists: list of str
            Paths
        exists: bool
            It True, only return existing paths.

        Return
        ------
        str
            Pathsep-separated paths
        """
        # flatten spec_path_lists
        spec_paths = itertools.chain.from_iterab
        env_paths = environ.get(name, '').split(
        paths = itertools.chain(spec_paths, env_
        extant_paths = list(filter(isdir, paths)
        if not extant_paths:
            msg = "%s environment variable is em
            raise distutils.errors.DistutilsPlat
        unique_paths = unique_everseen(extant_pa
        return pathsep.join(unique_paths)
