"""
Configuration Readers
"""

import os
from typing import Any

def read(filename: str, **kwargs) -> None:
    """
    Configuration Reader

    Execute a configuration script, passing only named variables to the script.
    Any modifications made to the objects will be reflected in the caller's
    objects.  For instance, lists and dictionaries may have entries added,
    removed or modified.

    It is not an error if the script does not exist; the objects will be
    unchanged.

    Parameters:
        filename (str): Configuration script
        **kwargs: ``Key=Value`` global variables available to the script.

    Example::

        CONFIG = {}
        OPTIONS = []
        mhi.common.config.read("~/.mhi.product.py",
                               CONFIG=CONFIG, OPTIONS=OPTIONS)

    Example Configuration Script::

        CONFIG['param'] = 'value'
        OPTIONS.append('-debug')
    """

    if not kwargs:
        raise ValueError("No global variables given")

    filename = os.path.expanduser(os.path.expandvars(filename))
    if os.path.isfile(filename):
        with open(filename) as file:
            exec(file.read(), kwargs)                # pylint: disable=exec-used

def fetch(filename: str, name: str = "OPTIONS", value: Any = None):
    """
    Configuration Reader

    Execute a configuration script, passing only one named object to the script.
    Any modifications made to the object will be reflected in the returned
    object.  For instance, dictionary entries added, removed or modified.

    It is not an error if the script does not exist; the object will be
    unchanged.

    Parameters:
        filename (str): Configuration script
        name (str): name of the script's global variable (Default: "OPTIONS")
        value: object passed to the script (Default: an empty dictionary)

    Returns:
        The configuration object

    Example::

        OPTIONS = mhi.common.config.fetch("~/.mhi.product.py")

    Example Configuration Script::

        OPTIONS['debug'] = True
    """

    if value is None:
        value = {}
    read(filename, **{name: value})

    return value
