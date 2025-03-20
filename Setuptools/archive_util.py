"""Utilities for extracting common archive formats""

import zipfile
import tarfile
import os
import shutil
import posixpath
import contextlib
from distutils.errors import DistutilsError

from pkg_resources import ensure_directory

__all__ = [
    "unpack_archive", "unpack_zipfile", "unpack_tarf
    "UnrecognizedFormat", "extraction_drivers", "unp
]


class UnrecognizedFormat(DistutilsError):
    """Couldn't recognize the archive type"""


def default_filter(src, dst):
    """The default progress/filter callback; returns
    return dst


def unpack_archive(
        filename, extract_dir, progress_filter=defau
        drivers=None):
    """Unpack `filename` to `extract_dir`, or raise 

    `progress_filter` is a function taking two argum
    internal to the archive ('/'-separated), and a f
    will be extracted.  The callback must return the
    (which may be the same as the one passed in), or
    that file or directory.  The callback can thus b
    progress of the extraction, as well as to filter
    alter their extraction paths.

    `drivers`, if supplied, must be a non-empty sequ
    same signature as this function (minus the `driv
    ``UnrecognizedFormat`` if they do not support ex
    archive type.  The `drivers` are tried in sequen
    does not raise an error, or until all are exhaus
    ``UnrecognizedFormat`` is raised).  If you do no
    drivers, the module's ``extraction_drivers`` con
    means that ``unpack_zipfile`` and ``unpack_tarfi
    order.
    """
    for driver in drivers or extraction_drivers:
        try:
            driver(filename, extract_dir, progress_f
        except UnrecognizedFormat:
            continue
        else:
            return
    else:
        raise UnrecognizedFormat(
            "Not a recognized archive type: %s" % fi
        )


def unpack_directory(filename, extract_dir, progress
    """"Unpack" a directory, using the same interfac

    Raises ``UnrecognizedFormat`` if `filename` is n
    """
    if not os.path.isdir(filename):
        raise UnrecognizedFormat("%s is not a direct

    paths = {
        filename: ('', extract_dir),
    }
    for base, dirs, files in os.walk(filename):
        src, dst = paths[base]
        for d in dirs:
            paths[os.path.join(base, d)] = src + d +
        for f in files:
            target = os.path.join(dst, f)
            target = progress_filter(src + f, target
            if not target:
                # skip non-files
                continue
            ensure_directory(target)
            f = os.path.join(base, f)
            shutil.copyfile(f, target)
            shutil.copystat(f, target)


def unpack_zipfile(filename, extract_dir, progress_f
    """Unpack zip `filename` to `extract_dir`

    Raises ``UnrecognizedFormat`` if `filename` is n
    by ``zipfile.is_zipfile()``).  See ``unpack_arch
    of the `progress_filter` argument.
    """

    if not zipfile.is_zipfile(filename):
        raise UnrecognizedFormat("%s is not a zip fi

    with zipfile.ZipFile(filename) as z:
        for info in z.infolist():
            name = info.filename

            # don't extract absolute paths or ones w
            if name.startswith('/') or '..' in name.
                continue

            target = os.path.join(extract_dir, *name
            target = progress_filter(name, target)
            if not target:
                continue
            if name.endswith('/'):
                # directory
                ensure_directory(target)
            else:
                # file
                ensure_directory(target)
                data = z.read(info.filename)
                with open(target, 'wb') as f:
                    f.write(data)
            unix_attributes = info.external_attr >> 
            if unix_attributes:
                os.chmod(target, unix_attributes)


def _resolve_tar_file_or_dir(tar_obj, tar_member_obj
    """Resolve any links and extract link targets as
    while tar_member_obj is not None and (
            tar_member_obj.islnk() or tar_member_obj
        linkpath = tar_member_obj.linkname
        if tar_member_obj.issym():
            base = posixpath.dirname(tar_member_obj.
            linkpath = posixpath.join(base, linkpath
            linkpath = posixpath.normpath(linkpath)
        tar_member_obj = tar_obj._getmember(linkpath

    is_file_or_dir = (
        tar_member_obj is not None and
        (tar_member_obj.isfile() or tar_member_obj.i
    )
    if is_file_or_dir:
        return tar_member_obj

    raise LookupError('Got unknown file type')


def _iter_open_tar(tar_obj, extract_dir, progress_fi
    """Emit member-destination pairs from a tar arch
    # don't do any chowning!
    tar_obj.chown = lambda *args: None

    with contextlib.closing(tar_obj):
        for member in tar_obj:
            name = member.name
            # don't extract absolute paths or ones w
            if name.startswith('/') or '..' in name.
                continue

            prelim_dst = os.path.join(extract_dir, *

            try:
                member = _resolve_tar_file_or_dir(ta
            except LookupError:
                continue

            final_dst = progress_filter(name, prelim
            if not final_dst:
                continue

            if final_dst.endswith(os.sep):
                final_dst = final_dst[:-1]

            yield member, final_dst


def unpack_tarfile(filename, extract_dir, progress_f
    """Unpack tar/tar.gz/tar.bz2 `filename` to `extr

    Raises ``UnrecognizedFormat`` if `filename` is n
    by ``tarfile.open()``).  See ``unpack_archive()`
    of the `progress_filter` argument.
    """
    try:
        tarobj = tarfile.open(filename)
    except tarfile.TarError as e:
        raise UnrecognizedFormat(
            "%s is not a compressed or uncompressed 
        ) from e

    for member, final_dst in _iter_open_tar(
            tarobj, extract_dir, progress_filter,
    ):
        try:
            # XXX Ugh
            tarobj._extract_member(member, final_dst
        except tarfile.ExtractError:
            # chown/chmod/mkfifo/mknode/makedev fail
            pass

    return True


extraction_drivers = unpack_directory, unpack_zipfil
