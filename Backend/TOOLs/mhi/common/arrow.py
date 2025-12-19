"""
This module is used to encode and decode between a ``set`` of compass directions
``{"N", "E", "SW" }`` and bit encoded values (``0b001001001``).

.. table:: Arrow directions
    :widths: auto

    ================= =====
    Direction         Value
    ================= =====
    N                     1
    S                     2
    W                     4
    E                     8
    NW                   16
    NE                   32
    SW                   64
    SE                  128
    ================= =====
"""

#===============================================================================
# Imports
#===============================================================================

from typing import Sequence, Union

from .codec import KeywordCodec



#===============================================================================
# Arrow CODEC
#===============================================================================

class Arrow(KeywordCodec):
    """
    Coder/Decoder for compass directions into PSCAD integer representation
    """

    _KEYS = {"arrows"}

    _DIR = {"N": 1, "S": 2, "W": 4, "E": 8,
            "NW": 16, "NE": 32, "SW": 64, "SE": 128}

    def encodes(self, keyword: str) -> bool:
        """
        Predicate, indicating whether or not this keyword codec will encode
        and decode a particular keyword

        Parameters:
            keyword (str): keyword to test

        Returns:
            bool: ``True`` if ``keyword`` is ``'arrows'``, ``False`` otherwise
        """

        return keyword in self._KEYS

    def encode(self, dirs: Union[int, str, Sequence[str]]) -> int: # pylint: disable=arguments-differ
        """
        Encode one or more directions into an bit-encoded integer::

            >>> arrow.encode("N S")
            3
            >>> arrow.encode(["E", "W"])
            12

        Parameters:
            dirs: the directions to encode

        Returns:
            int: a bit-encoded direction value
        """

        if dirs:
            if isinstance(dirs, int):
                return dirs
            if isinstance(dirs, str):
                dirs = dirs.split()
            return sum(self._DIR[direction.upper()] for direction in dirs)

        return 0

    def decode(self, dirs: Union[str, int]) -> str:       # pylint: disable=arguments-differ
        """
        Decode a bit-encoded integer string into a direction string::

            >>> arrow.decode("15")
            'N S W E'

        Parameters:
            dirs (str): the direction value to decode

        Returns:
            str: a space-separated list of compass directions
        """

        if isinstance(dirs, str):
            dirs = int(dirs)

        return " ".join(key
                        for key, val in self._DIR.items() if (dirs & val) != 0)
