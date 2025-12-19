#! /usr/bin/env python3
"""
Encode user-friendly values into internal formats used by the application,
and decoder the values back into user-friendly values.
"""

#===============================================================================
# Imports
#===============================================================================

from typing import Any, Tuple, FrozenSet, Dict
from warnings import warn


#===============================================================================
# Coder/Decoder
#===============================================================================

class Codec:

    """
    Codec: Coder / Decoder

    Encode from user-friendly values into an internal value format,
    and decode from the internal format into (ideally) a user-friendly
    value.
    """

    def encode(self, value: Any) -> Any: # pylint: disable=unused-argument,no-self-use
        """
        Encode a user-friendly value into an internal format

        Parameters:
           value: the value to encode

        Returns:
            the encoded value
        """

        raise NotImplementedError()

    def decode(self, value: Any) -> Any: # pylint: disable=unused-argument,no-self-use
        """
        Decode an internal format value into a more user-friendly format

        Parameters:
           value: the value to decode

        Returns:
            the decoded value
        """

        raise NotImplementedError()


#===============================================================================
# Boolean Coder/Decoder
#===============================================================================

class BooleanCodec(Codec):

    """
    Boolean Coder / Decoder

    Convert Python boolean values to/from the strings `"true"` and `"false"`,
    used by MHI application serialization.
    """

    def encode(self, value: Any) -> str:
        """
        Encode a boolean into an MHI serialization string

        Parameters:
           value (bool): the value to encode

        Returns:
            str: the "encoded" string `"true"` or `"false"`
        """

        flag = None
        if isinstance(value, bool):
            flag = value
        elif isinstance(value, str):
            if value.lower() in {"false", "no", "0"}:
                flag = False
            elif value.lower() in {"true", "yes", "1"}:
                flag = True
        elif isinstance(value, int):
            if value == 0:
                flag = False
            elif value == 1:
                flag = True

        if flag is None:
            raise ValueError("Not a boolean value: "+repr(value))

        if not isinstance(value, bool):
            warn("Not a boolean value: " + repr(value), stacklevel=6)

        return "true" if flag else "false"

    def decode(self, value: str) -> bool:
        """
        Decode a boolean from an MHI serialization string

        Parameters:
           value (str): the string `"true"` or `"false"`

        Returns:
            bool: the decoded value
        """

        return value.lower() == "true"

    @staticmethod
    def range() -> Tuple[bool, bool]:
        """
        Returns the range of values that this codec will encode,
        as in, maybe passed to :meth:`.encode` and will
        be returned by :meth:`.decode`.

        Returns:
            Tuple[Bool, Bool]: ``False, True``
        """

        return False, True


#===============================================================================
# Map Coder/Decoder
#===============================================================================

class MapCodec(Codec):

    """
    Map Coder / Decoder

    Convert Python values to/from the strings,
    used by MHI application serialization.
    """

    def __init__(self, code, *, extras=None):
        self._encode = code
        self._decode = {val: key for key, val in code.items()}
        self._range = frozenset(self._encode.keys())
        if extras:
            for extra_code, values in extras.items():
                for value in values:
                    self._encode[value] = extra_code

    def encode(self, value: Any) -> str:
        """
        Encode a value into an MHI serialization string

        Parameters:
           value: the value to encode

        Returns:
            str: the encoded string
        """

        if value not in self._encode:
            encoded = str(value)
            if encoded in self._decode:
                return encoded
            if encoded in self._encode:
                value = encoded

        return self._encode[value]

    def decode(self, value: str) -> Any:
        """
        Decode a boolean from an MHI serialization string

        Parameters:
           value (str): the value to decode

        Returns:
            the decoded value
        """

        return self._decode[value]

    def range(self) -> FrozenSet[Any]:
        """
        Returns the range of values that this codec will encode,
        as in, maybe passed to :meth:`.encode` and will
        be returned by  :meth:`.decode`.

        Returns:
            frozenset: value which can be encoded by the codec.
        """

        return self._range

    def __repr__(self):
        code = ", ".join("{!r}: {!r}".format(val, key)
                         for key, val in self._decode.items())
        return "MapCodec({{{}}})".format(code)


#===============================================================================
# Keyword Coder/Decoder
#===============================================================================

class KeywordCodec(Codec):

    """
    Keyword Codec

    Encode values for specific keys of a dictionary from user-friendly values
    into an internal value format, and decode values for those specific keys
    from the internal format into (ideally) a user-friendly value.
    """

    def encodes(self, keyword: str): # pylint: disable=unused-argument,no-self-use
        """
        Predicate, indicating whether or not this keyword codec will encode
        and decode a particular keyword

        Parameters:
            keyword (str): keyword to test

        Returns:
            bool: ``True`` if this codec handles the ``keyword``,
            ``False`` otherwise
        """

        raise NotImplementedError()

    def encode_all(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encode all values in the given dictionary which are handled by this
        codec.  Values for unrecognized keywords are unchanged.

        Parameters:
            kwargs (dict): a dictionary of keyword-value pairs

        Returns:
            dict: A new dictionary containing encoded values, where supported.
        """

        return {key: self.encode(value) if self.encodes(key) else value
                for key, value in kwargs.items()}

    def decode_all(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode all values in the given dictionary which are handled by this
        codec.  Values for unrecognized keywords are unchanged.

        Parameters:
            kwargs (dict): a dictionary of keyword-value pairs

        Returns:
            dict: A new dictionary containing decoded values, where supported.
        """

        return {key: self.decode(value) if self.encodes(key) else value
                for key, value in kwargs.items()}


#===============================================================================
# Coder/Decoder
#===============================================================================

class SimpleCodec(KeywordCodec):
    """
    Keyword Codec

    Encode values for specific keys of a dictionary from user-friendly values
    into an internal value format, and decode values for those specific keys
    from the internal format into (ideally) a user-friendly value.

    Parameters:
        code_dict (dict): A dictionary used to translate user-friendly values
          into internal values.
        **codes: additional keyword-value translation pairs.

    Example:
        A codec which converts fruit names into integers::

			>>> codec = SimpleCodec(apple=1, banana=2, pear=3)
			>>> codec.keywords('fruit')
			>>> codec.encode('apple')
			1
			>>> codec.decode(2)
			'banana'
			>>> codec.encode_all({'animal': 'lion', 'fruit': 'pear'})
			{'animal': 'lion', 'fruit': 3}
    """

    def __init__(self, code_dict=None, **codes):

        if code_dict is None:
            self._code = dict(**codes)
        else:
            self._code = dict(code_dict, **codes)
        self._decode = {str(val): key for key, val in self._code.items()}
        self._keys = set()

    def alternates(self, code_dict, **codes):
        """
        Provide additional encodings aliases for the codec.
        These additional options must not duplicate any existing user-friendly
        keywords, and must not introduce any new values to the mapping.

        For instance, a codec may defined the mapping 'EMTPY' => 0.
        An alternate mapping 'BLANK' => 0 may be provided, allowing either
        'EMPTY' or 'BLANK' to be encoded as 0, but 0 will always be decoded
        as 'EMPTY'.

        Parameters:
            code_dict (dict): A dictionary of additional translation aliases.
            **codes: additional keyword-value translation alias pairs.
        """
        alt = dict(code_dict, **codes)
        alt_decode = {str(val): key for key, val in alt.items()}

        dup = self._code.keys() & alt.keys()
        if dup:
            raise ValueError("Alternate contains duplicate keys: %s" % dup)

        new_vals = alt_decode.keys() - self._decode.keys()
        if new_vals:
            raise ValueError("Alternate contains new values: %s" % new_vals)

        self._code.update(alt)
        alt_decode.update(self._decode)
        self._decode = alt_decode

    def encode(self, value):
        return self._code[value]

    def decode(self, value):
        return self._decode[str(value)]

    def keywords(self, *keywords: str) -> None:
        """
        Add keywords which will be recognized by this codec when
        :meth:`.encode_all()` or :meth:`.decode_all()` is called.

        Parameters:
            *keywords (str): List of keywords to associate to this codec
        """

        self._keys |= set(keywords)

    def encodes(self, keyword: str) -> bool:
        return keyword in self._keys
