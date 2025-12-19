#! /usr/bin/env python3
"""
Conversion between pathnames with and without expanded %ENVIRONMENT_VARIABLES%.
"""

import os
from typing import Dict, List, Sequence, Tuple

#===============================================================================
# When run from IDLE, if the HOME environment is not set, Tkinter is setting it
# to %HOMEDRIVE%%HOMEPATH% ... which can be wrong under Windows.
#    https://bugs.python.org/issue27263
# Attempt to detect and restore to correct default
#===============================================================================

if os.name == 'nt':
    import sys
    if 'idlelib' in sys.modules:
        if os.getenv('HOME') == os.getenv('HOMEDRIVE', '') + os.getenv('HOMEPATH', ''):
            try:
                os.environ['HOME'] = os.getenv('USERPROFILE', '')
            except KeyError:
                del os.environ['HOME']


#===============================================================================
# Expand Path
#===============================================================================

def expand_path(path: str, abspath: bool = False, folder: str = None) -> str:
    """
    Expand ``path``, by replacing a `~` or `~user` prefix, as well as
    expanding any `$var`, `${var}` and `%var%` patterns in the path.

    Parameters:
        path (str): The path to be expanded.
        abspath (bool): If `True`, convert resulting path to an absolute path.
        folder (str): If provided, the path to the filename is resolved
            relative to this folder.

    Returns:
        str: The expanded ``path``, optionally forced to an absolute path.
    """

    if folder:
        path = os.path.join(folder, path)

    path = os.path.normpath(os.path.expanduser(os.path.expandvars(path)))
    if abspath:
        path = os.path.abspath(path)

    return path

def expand_paths(paths: Sequence[str], abspath: bool = False,
                 folder: str = None) -> List[str]:
    """
    Expand ``paths``, by replacing a `~` or `~user` prefix, as well as
    expanding any `$var`, `${var}` and `%var%` patterns in the paths.

    Parameters:
        path (List[str]): A list of paths to be expanded.
        abspath (bool): If `True`, convert resulting paths to absolute paths.
        folder (str): If provided, the paths to the filenames are resolved
            relative to this folder.

    Returns:
        List[str]: A list of expanded ``paths``, optionally forced to
        absolute paths.
    """

    return [expand_path(path, abspath, folder) for path in paths]


#===============================================================================
# Contract Path
#===============================================================================

def contract_path(path: str, *, keys: List[str] = None, # pylint: disable=too-many-branches
                  reverse_map: Dict[str, str] = None) -> str:
    """contract_path(path)

    Look for and replace any substring of the path that matches a value
    found in an environment variable with that environment variable:
    `${key}` or `%key%`.  Additionally, replace a path starting with
    the user's home path with `~`.

    Parameters:
        path (str): The path to be shortened by replacing parts with
           environment variables.

    Returns:
        str: The contracted ``path``.
    """

    keys = keys or []
    reverse_map = reverse_map or {}

    if len(keys) == 0:
        for key, val in os.environ.items():
            if ';' in val:
                continue
            if os.name == 'nt':
                key = "%{0}%".format(key)
            else:
                key = "${%s}" % key

            if len(key) < len(val) or key == '%HOME%':
                if val not in reverse_map  or  len(key) < len(reverse_map[val]):
                    reverse_map[val] = key

        keys.extend(sorted(reverse_map.keys(), key=len, reverse=True))

    for text in keys:
        path = path.replace(text, reverse_map[text])

    if path in {"${HOME}", "%HOME%", "${USERPROFILE}", "%USERPROFILE%"}:
        path = "~"
    elif path.startswith("%HOME%\\"):
        path = os.path.join("~", path[7:])
    elif path.startswith("${HOME}/"):
        path = os.path.join("~", path[8:])
    elif path.startswith("%USERPROFILE%\\"):
        path = os.path.join("~", path[14:])
    elif path.startswith("${USERPROFILE}/"):
        path = os.path.join("~", path[15:])

    return os.path.normpath(path)

def contract_paths(paths):
    """
    Look for and replace any substring of the paths that matches a value
    found in an environment variable with that environment variable:
    `${key}` or `%key%`.  Additionally, replace paths starting with
    the user's home path with `~`.

    Parameters:
        paths (List[str]): The paths to be shortened by replacing parts with
           environment variables.

    Returns:
        List[str]: A list of contracted ``paths``.
    """

    return [contract_path(path) for path in paths]


#===============================================================================
# Self test
#===============================================================================

if __name__ == "__main__":

    PATHS = [r'%LOCALAPPDATA%\Manitoba HVDC Research Centre\Enerplot',
             r'%PUBLIC%\Documents\Enerplot\1.0\Examples\EnerplotExamples.pswx',
             r'%TMP%\tempfile',
             r'~\my\doc',
             r'~']

    PATHS1 = expand_paths(PATHS)
    PATHS2 = contract_paths(PATHS1)

    for p, p1, p2 in zip(PATHS, PATHS1, PATHS2):
        assert p != p1, "expand('%s') == '%s': must differ" % (p, p1)
        assert p == p2, "'%s' expands to '%s' contacts to '%s'" % (p, p1, p2)
