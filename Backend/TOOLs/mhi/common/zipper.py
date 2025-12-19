import os, sys
import mhi.common.process

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import DefaultDict, Dict, List, NamedTuple, Set, NewType
from zipfile import PyZipFile

Version = NewType('Version', str)

class Error(Exception):
    pass

class LibraryZipper:
    """
    Collect python packages together and save as a zipped library.
    The python modules may be pre-compiled for a particular CPython version.
    """

    SUB_COMMAND = "update"

    def __init__(self, app_name: str, *packages: str, lib: str = 'mhi.zip',
                 allow_all: bool = True, allow_local: bool = True):
        self._app_name = app_name
        self._packages = {}
        self._exclude_files = {'__main__.py'}
        self._exclude_paths = {__name__.replace('.', '\\') + '.py'}
        self._lib = lib
        self._all = allow_all
        self._local = allow_local

        for package in packages:
            self.add_package(package)

    def add_package(self, package: str) -> None:
        """
        Add a package to the set of packages to be included in the
        zipped library.
        """

        self._packages[package] = Path(sys.modules[package].__path__[0])

    def add_subparser(self, subparsers) -> None:
        """
        Create and add a subparser for creation of an embedded library.
        """

        updater = subparsers.add_parser(self.SUB_COMMAND,
                                        help="Update embedded library")

        updater.set_defaults(func=self._update,
                             help=[self.SUB_COMMAND, '--help'])
        updater.add_argument('-b', '--binary', action='store_true',
                             help="generate a pre-compiled embedded library")
        updater.add_argument('-s', '--source', action='store_true',
                             help="generate a source-code embedded library")
        updater.add_argument('version', nargs='*',
                             help=self._app_name + " version(s) to update")

    def _update(self, args: Namespace) -> None:
        """
        Subparser command

        For the version indicated, create the embedded zip library
        """

        try:
            versions = self.parse_versions(args.version)

            if args.binary:
                self._validate_binary_compatibility(versions)

            zipfiles = self._get_zipfiles(versions)
            self._write_zipfiles(zipfiles, args)
        except Error as err:
            print(err, file=sys.stderr)


    #===========================================================================
    # Application versions
    #===========================================================================

    def parse_versions(self, update_versions: List[str]) -> Dict[Version, Path]:
        """
        Return a dictionary of selected application versions and their paths.

        If the 'all' version is requested, return all versions.
        If a 'local' version is requested, return just the local directory.
        """

        versions = self.get_versions()

        choices = self._validate_versions(versions)

        if len(update_versions) == 0:
            raise Error("Specify version: " + choices)

        if self._local and update_versions == ['local']:
            versions = {'local': Path('.')}

        elif not self._all or update_versions != ['all']:
            unknowns = {ver for ver in update_versions if ver not in versions}
            if unknowns:
                raise Error("No such version(s): " + ", ".join(unknowns)
                            + "\nUse " + choices)
            versions = {ver: versions[ver] for ver in update_versions}

        return versions


    def get_versions(self) -> Dict[Version, Path]:
        """
        Return a dictionary of installed application versions and their paths.

        32-bit versions are identified with a '-32' suffix on the key,
        64-bit versions do not have any suffix.
        """

        v32, v64 = mhi.common.process._exe_path(self._app_name)

        paths = {ver + '-32': Path(path).parent for ver, path in v32.items()}
        for version, path in v64.items():
            paths[version] = Path(path).parent

        versions = {version: path for version, path in paths.items()
                    if self._get_zipfile(path).exists()}

        return versions


    def _validate_versions(self, versions: Dict[Version, Path]) -> str:
        """
        Convert a dictionary of versions into a string describing the
        valid version identifiers.
        """

        if len(versions) == 0:
            raise Error("No installed " + self._app_name + " versions detected")

        choices = "all, " if self._all else ""
        if self._local:
            choices = choices + "local, "

        if choices:
            choices = choices + "or "

        if len(versions) > 1:
            choices = choices + "one or more of "

        choices = choices + ", ".join(versions)

        return choices


    #===========================================================================
    # Ensure correct version of Python is used for precompiled libraries
    #===========================================================================

    def _validate_binary_compatibility(self, versions: Dict[Version, Path]):
        """
        For each version, excluding a 'local' version, determine the version
        of Python the embedded library must be compiled with to be useful.
        If the current Python environment does not match the require version,
        raise an error decribing the mis-matches.
        """

        if sys.implementation.cache_tag is None:
            raise Error("Caching of *.pyc file is not supported.")

        if not sys.implementation.cache_tag.startswith("cpython-"):
            raise Error("CPython is required for creating binary library")

        prefix = "python" + sys.implementation.cache_tag[8:]
        exts = {".dll", "._pth", ".zip"}

        incompatible = {}
        for tag, path in versions.items():
            if tag == 'local':
                continue

            if any(not (path / (prefix + ext)).is_file() for ext in exts):
                vers = DefaultDict(set)
                for file in path.glob("python3?.*"):
                    vers[file.stem].add(file.suffix)

                incompatible[tag] = max((ver for ver, suffixes in vers.items()
                                         if exts <= suffixes),
                                        default="<unknown version>")
        if incompatible:
            msg = ("Current version: " + prefix + "\n" +
                   "\n".join("Requires " + ver +
                             " to compile embedded library for " + tag
                             for tag, ver in incompatible.items()))
            raise Error(msg)


    #===========================================================================
    # Version(s) to library zip file(s)
    #===========================================================================

    def _get_zipfiles(self, versions: Dict[Version, Path]) -> List[Path]:
        """
        Return the list of library zipfiles from the dictionary of versions
        """

        return [self._get_zipfile(path) for path in versions.values()]

    def _get_zipfile(self, path: Path) -> Path:
        """
        Return the library zipfile path for a give application path
        """

        return path / self._lib


    #===========================================================================
    # Zipfile writing
    #===========================================================================

    def _write_zipfiles(self, zipfiles: List[Path], args: Namespace) -> None:
        """
        Create the library zipfiles based on source & binary argment options.
        """

        binary = args.binary
        source = args.source or not binary

        errors = False
        for zipfile in zipfiles:
            try:
                self._write_zipfile(zipfile, source, binary)
            except OSError as err:
                print(err, file=sys.stderr)
                errors = True

        if errors:
            raise Error("Failed to write one or more zip libraries.\n"
                        "  Running as Administrator may be required.")


    def _write_zipfile(self, zipfile: Path, include_source: bool = True,
              compile_source: bool = False) -> None:
        """
        Create a source and/or binary library zipfile.
        """


        if not (include_source or compile_source):
            raise Error("Source must be included, compiled or both")

        with PyZipFile(zipfile, 'w') as zf:
            print('Writing', zipfile)
            self._write_namespaces(zf)
            if include_source:
                self._write_source(zf)
            if compile_source:
                self._compile_source(zf)

    def _write_namespaces(self, zf) -> None:
        """
        Ensure namespace packages have an __init__.py file in the zip library,
        so the zipfile is treated as a package library.
        """
        for init_py in self._init_py_files():
            zf.writestr(init_py, "")

    def _init_py_files(self) -> Set[str]:
        """
        Identify __init__.py files necessary to turn namespaces into packages.
        """

        init_pys = set()
        for package in self._packages:
            segments = package.split('.')
            init_pys.update('/'.join(segments[:last]) + '/__init__.py'
                            for last in range(1, len(segments)))
        return init_pys

    def _write_source(self, zf):
        """
        Write package sources in the zipfile
        """

        for name, path in self._packages.items():
            self._write_package(zf, name, path)

    def _write_package(self, zf, name, path):
        """
        Write all source files in a package into the zipfile
        """

        base = path.parents[name.count('.')]
        for file in path.rglob('*.py'):
            if file.name not in self._exclude_files:
                archive_path = file.relative_to(base)
                if str(archive_path) not in self._exclude_paths:
                    zf.write(file, archive_path)

    def _compile_source(self, zf):
        """
        Compile *.py source files into *.pyc files in the zipfile
        """

        def not_excluded(filename):
            if os.path.basename(filename) in self._exclude_files:
                return False
            if filename[offset:] in self._exclude_paths:
                return False
            return True

        for name, path in self._packages.items():
            base = path.parents[name.count('.')]

            offset = len(str(base)) + 1
            basename = path.parent.relative_to(base)
            if str(basename) == '.':
                basename = ''
            zf.writepy(path, basename, filterfunc=not_excluded)
