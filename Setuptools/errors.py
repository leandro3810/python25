"""setuptools.errors

Provides exceptions used by setuptools modules.
"""

from distutils.errors import DistutilsError


class RemovedCommandError(DistutilsError, Runtim
    """Error used for commands that have been re

    Since ``setuptools`` is built on ``distutils
    from ``setuptools`` will make the behavior f
    error is raised if a command exists in ``dis
    removed in ``setuptools``.
    """
