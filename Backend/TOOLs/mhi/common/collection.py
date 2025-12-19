#! /usr/bin/env python3
"""
General purpose utilities
"""

#===============================================================================
# Imports
#===============================================================================

import collections, itertools

#===============================================================================
# Indexable Dictionary
#===============================================================================

class IndexableDict(collections.OrderedDict):

    """
    An ordered dictionary, where values can be retrieved by index as well
    as by key::

        >>> idict = IndexableDict([('foo', 10), ('bar', 30), ('baz', 20)])
        >>> idict['foo'] == idict[0] == idict[-3] == 10
        True
        >>> idict['bar'] == idict[1] == idict[-2] == 30
        True
        >>> idict['baz'] == idict[2] == idict[-1] == 20
        True
    """

    def __getitem__(self, key):
        """
        If `key` is an integer, retrieve the value at that index.
        Otherwise, retrieve the value with the given `key`
        """

        if isinstance(key, int):
            num = len(self)
            if key < -num or key >= num:
                raise IndexError()
            idx = key if key >= 0 else num + key
            return next(itertools.islice(self.values(), idx, idx + 1))
        return super().__getitem__(key)


#===============================================================================
# Unit tests
#===============================================================================

if __name__ == '__main__':
    d = IndexableDict([('foo', 10), ('bar', 30)])
    d['baz'] = 20

    assert d['foo'] == d[0] == d[-3] == 10
    assert d['bar'] == d[1] == d[-2] == 30
    assert d['baz'] == d[2] == d[-1] == 20

    try:
        assert d[3] and False, "IndexError expected: 3 is out of range."
    except IndexError:
        pass
    try:
        assert d[-4] and False, "IndexError expected: -4 is out of range."
    except IndexError:
        pass

    # keys and values are ordered...
    assert tuple(d.keys()) == ('foo', 'bar', 'baz')
    assert tuple(d.values()) == (10, 30, 20)
