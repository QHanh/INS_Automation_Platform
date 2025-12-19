"""
The `mhi.common` library is a package of common functions, which facilitate
the automation of various MHI applications from Python scripts.

This package is not intended to be used directly.  It will be used
internally by the application specific packages.
"""

VERSION = '2.3.3'
VERSION_HEX = 0x020303f0

__all__ = [] # type: ignore

def version_msg():
    """
    Common Library Version Message
    """

    return ("MHI Common Library v{}\n"
            "(c) Manitoba Hydro International Ltd.").format(VERSION)
