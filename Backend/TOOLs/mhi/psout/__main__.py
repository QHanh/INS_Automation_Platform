"""
PSCAD-Python Cosimulation
"""

import os
import sys
from pathlib import Path

import mhi.psout


def show_version():
    """
    Display version message"
    """

    print(f"MHI PSOut Library v{mhi.psout.__version__}")
    print("(c) Manitoba Hydro International Ltd.")
    print()


def open_help():
    """
    Open the help document
    """

    path = Path(__file__).parent / 'mhi-psout.chm'
    if path.is_file():
        os.startfile(path)
    else:
        print(f"Help file not found: {path}", file=sys.stderr)


def main():
    """
    Command Line processor
    """

    args = sys.argv[1:]
    if args in ([], ['version']):
        show_version()
    elif args == ['help']:
        open_help()
    else:
        print()
        print("Usage:")
        print("    py -m mhi.psout [subcommand]")
        print()
        print("Available subcommands:")
        print("    version   - display module version number (default)")
        print("    help      - open help for this module")
        print()


if __name__ == '__main__':
    main()
