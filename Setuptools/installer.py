import glob
import os
import subprocess
import sys
import tempfile
from distutils import log
from distutils.errors import DistutilsError

import pkg_resources
from setuptools.wheel import Wheel


def _fixup_find_links(find_links):
    """Ensure find-links option end-up being
    if isinstance(find_links, str):
        return find_links.split()
    assert isinstance(find_links, (tuple, li
    return find_links


def fetch_build_egg(dist, req):  # noqa: C90
    """Fetch an egg needed for building.

    Use pip/wheel to fetch/build a wheel."""
    # Warn if wheel is not available
    try:
        pkg_resources.get_distribution('whee
    except pkg_resources.DistributionNotFoun
        dist.announce('WARNING: The wheel pa
    # Ignore environment markers; if supplie
    req = strip_marker(req)
    # Take easy_install options into account
    # pip environment variables (like PIP_IN
    # take precedence.
    opts = dist.get_option_dict('easy_instal
    if 'allow_hosts' in opts:
        raise DistutilsError('the `allow-hos
                             'when using pip
    quiet = 'PIP_QUIET' not in os.environ an
    if 'PIP_INDEX_URL' in os.environ:
        index_url = None
    elif 'index_url' in opts:
        index_url = opts['index_url'][1]
    else:
        index_url = None
    find_links = (
        _fixup_find_links(opts['find_links']
        else []
    )
    if dist.dependency_links:
        find_links.extend(dist.dependency_li
    eggs_dir = os.path.realpath(dist.get_egg
    environment = pkg_resources.Environment(
    for egg_dist in pkg_resources.find_distr
        if egg_dist in req and environment.c
            return egg_dist
    with tempfile.TemporaryDirectory() as tm
        cmd = [
            sys.executable, '-m', 'pip',
            '--disable-pip-version-check',
            'wheel', '--no-deps',
            '-w', tmpdir,
        ]
        if quiet:
            cmd.append('--quiet')
        if index_url is not None:
            cmd.extend(('--index-url', index
        for link in find_links or []:
            cmd.extend(('--find-links', link
        # If requirement is a PEP 508 direct
        # the URL to pip, as `req @ url` doe
        # command line.
        cmd.append(req.url or str(req))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError
            raise DistutilsError(str(e)) fro
        wheel = Wheel(glob.glob(os.path.join
        dist_location = os.path.join(eggs_di
        wheel.install_as_egg(dist_location)
        dist_metadata = pkg_resources.PathMe
            dist_location, os.path.join(dist
        dist = pkg_resources.Distribution.fr
            dist_location, metadata=dist_met
        return dist


def strip_marker(req):
    """
    Return a new requirement without the env
    calling pip with something like `babel; 
    would always be ignored.
    """
    # create a copy to avoid mutating the in
    req = pkg_resources.Requirement.parse(st
    req.marker = None
    return req
