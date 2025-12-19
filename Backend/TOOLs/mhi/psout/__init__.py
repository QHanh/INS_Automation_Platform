#===============================================================================
# Manitoba Hydro International / Power Technology Center
# mhi.psout package
#===============================================================================

"""
A ``*.psout`` file reader library.

The PSOUT file is a binary file that contains one or more collections
of traces.  Each trace is a 1-d vector of data.  A trace may have an
associated "domain" trace with the same length.  Different traces are
identified by a location in a "call tree".  All trace collections,
known as "runs" share the same call tree, although a trace may not
exist at every location of the call tree in different runs.
"""


#==============================================================================
# Imports & Exports
#------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Iterator, Union
from weakref import WeakValueDictionary

try:
    import mhi.psout._psout as _psout
except ModuleNotFoundError:
    import _psout # For debug builds only

__all__ = ['File', 'Call', 'Trace', 'Run']


_VERSION = (1, 0, 5)

_TYPE = 'f0'

__version__ = '{0}.{1}.{2}'.format(*_VERSION, _TYPE)
__version_hex__ = int.from_bytes((*_VERSION, int(_TYPE, 16)), byteorder='big')


#==============================================================================
# Variable List as a Dictionary
#------------------------------------------------------------------------------

class VarListMixin:

    def variables(self) -> Dict[str, Any]:
        """
        Retrieve the key=value attributes stored with this object as a
        dictionary.

        If only a single variable value is required, ``item["VariableName"]``
        may be used to fetch just that value.
        """

        return self._variables()

    def _key_val(self):
        variables = self.variables()
        return ', '.join(f"{key}={val!r}" for key, val in variables.items())


#==============================================================================
# File
#------------------------------------------------------------------------------

class File(_psout.File, VarListMixin):
    """
    A PSOUT file object

    The PSOUT file contains a "Call Stack" and a list of "Runs".
    The "Call Stack" describes a tree of calls into which traces are organized,
    and is shared by all runs.  The traces themselves are stored in distinct
    "Runs".  A trace can only be retrieved given both a run and a call.

    The file must be closed when no longer in use.  To assist, `File`
    implements the context manager interface, so it may be used in a
    `with` statement so that it is automatically closed.

    Example::

        with mhi.psout.File("Cigre.psout") as file:
            ac_voltage_a_call = file.call("Root/Main/AC Voltage/Record/1")
            run = file.run(0)
            va = run.trace(ac_voltage_a_call)
            time = va.domain
            matplotlib.pyplot.plot(time.data, va.data, label="Phase A voltage")
    """

    __slots__ = ()

    #---------------------------------------------------------------------------
    # Calls
    #---------------------------------------------------------------------------

    def call(self, *path: Union[int, str], sep='/') -> Call:
        """
        Retrive a call from the given path in the call stack / tree

        Parameters:
            path: The call path, as names or ids
            sep: A delimiter string, used when single string argument is given

        Examples::
        
            call = file.call("Root/Main/AC Voltage/Record/1", sep="/")
            call = file.call("Root", "Main", "AC Voltage", "Record", 1)

        Note:
            A path segment composed entirely of digits is converted to an
            integer and used as a call id.
        """

        node = self.root

        if len(path) == 1 and sep and isinstance(path[0], str):
            if path[0].startswith('/'):
                path[0] = path[0][1:]
            path = path[0].split(sep)

        for segment in path:
            node = node.call(segment)

        return node

    def call_tree(self, width: int = None) -> None:
        """
        Print the call tree of the .psout file
        """

        def show(node, indent):
            s = f"{indent}{node.id} {node._key_val()}"
            if width and len(s) > width:
                s = s[:width-3] + "..."
            print(s)

            indent += "  "
            for call in node.calls():
                show(call, indent)

        print("Call Tree:")
        show(self.root, "  ")

    #---------------------------------------------------------------------------
    # Runs
    #---------------------------------------------------------------------------

    def runs(self) -> Iterator[Run]:
        """
        Return the runs stored in the .psout file
        """

        for i in range(self.num_runs):
            yield self.run(i)

    def run(self, index: int) -> Run:
        """
        Get the nth run in the .psout file
        """
        
        return self._get_run(index)

    def fetch_run(self, run_id: int) -> Run:
        """
        Fetch the run with the specified `id`.
        """
        
        return self._fetch_run(run_id)

    def run_list(self, *, width: int = None, traces: bool = False) -> None:
        """
        Print all of the runs stored in the .psout file

        Parameters:
            width (int): Limit output to given number of characters
            traces (bool): If `True`, also out traces stored in each run
        """

        for run_num, run in enumerate(self.runs()):
            s = f"Run #{run_num}/{self.num_runs} {run._key_val()}"
            if width and len(s) > width:
                s = s[:width-3] + "..."
            print(s)

            if traces:
                run.trace_list(width=width)
                print()

    #---------------------------------------------------------------------------
    # Misc
    #---------------------------------------------------------------------------

    def __getitem__(self, key):
        """
        Fetch a run by `index` or a variable by `Name`.

        If `key` is an `int`, the run is fetched by index.
        If `key` is a `str`, the named variable is returned.
        """

        if isinstance(key, str):
            return self._var(key)
        if isinstance(key, int):
            return self.get_run(key)
        raise KeyError("Invalid subscript: {key!r}")

    def __repr__(self):
        return f"File[{self.path!r}, {self._key_val()}]"

_psout.File = File


#==============================================================================
# Call
#------------------------------------------------------------------------------

class Call(_psout.Call, VarListMixin):
    """
    A Call in the global call tree of the file.

    All calls other than the root call node will have a parent.
    Every call may have child subcalls, which in turn can have grandchildren,
    great-grandchildern, and so on.
    """

    __slots__ = ()

    def calls(self) -> Iterator[Call]:
        """
        Return the subcall children of the current node
        """

        for i in range(self.num_calls):
            yield self._get(i)

    def call(self, child: Union[int, str]) -> Call:
        """
        Return a subcall of the current node, identified by either
        an id number, or a name.

        Parameters:
            child: the `id` or `"Name"` of a subcall
        """

        if isinstance(child, int):
           return self._fetch(child)

        if isinstance(child, str):
            if child.isdecimal():
                return self._fetch(int(child))
            if child in {'', '.'}:
                return self._get(0)
            if child == '..':
                return self.parent

            for call in self.calls():
                if call['Name'] == child:
                    return call

        raise KeyError(f"Unknown child: {child!r}")

    def __getitem__(self, key):
        """
        Fetch a subcall by `index` or a variable by `Name`.

        If `key` is an `int`, the subcall is fetched by index.
        If `key` is a `str`, the named variable is returned.
        """

        if isinstance(key, str):
            return self._var(key)
        if isinstance(key, int):
            return self._get(key)
        raise KeyError("Invalid subscript: {key!r}")

    def __repr__(self):
        variables = self.variables()
        key_val = ', '.join(f"{key}={val!r}" for key, val in variables.items())
        return f"Call[#{self.id}, {self._key_val()}]"

_psout.Call = Call


#==============================================================================
# Run
#------------------------------------------------------------------------------

class Run(_psout.Run, VarListMixin):
    """
    A handle to a run set in the file.  A run set is a collection of
    traces that match the set structure defined by the call nodes
    """

    __slots__ = '_traces',
    _traces: WeakValueDictionary[int, Trace]

    def __init__(self, file: File):
        super().__init__(file)
        self._traces = WeakValueDictionary()

    def _register(self, trace):
        return self._traces.setdefault(trace.id, trace)

    def trace(self, ident: Union[int, Call]) -> Trace:
        """
        Return a trace from this run identified by index or call.

        Parameters:
            ident: the `index` or `call` of the trace
        """

        trace = super().trace(ident)
        return self._register(trace)

    def traces(self) -> Iterator[Trace]:
        """
        Return the traces of this run
        """

        for i in range(self.num_traces):
            yield self.trace(i)

    def trace_list(self, width: int = None) -> None:
        """
        Print all of the traces held within this run.
        """

        for trace_num, trace in enumerate(self.traces()):
            s = f"#{trace_num}: {trace} {trace._key_val()}"
            if width and len(s) > width:
                s = s[:width-3] + "..."
            print(s)

    def call(self, *args, sep="/") -> Trace:
        """
        Retrive a trace from this run for the given call path.

        Parameters:
            path: The call path, as names or ids
            sep: A delimiter string, used when single string argument is given

        Examples::
        
            trace = run.call("Root/Main/AC Voltage/Record/1", sep="/")
            trace = run.call("Root", "Main", "AC Voltage", "Record", 1)

        Note:
            A path segment composed entirely of digits is converted to an
            integer and used as a call id.
        """

        call = self.file.call(*args, sep="/")
        return self.trace(call)

    def __repr__(self):
        return f"Run[#{self.id}, {self._key_val()}]"

_psout.Run = Run


#==============================================================================
# Trace
#------------------------------------------------------------------------------

class Trace(_psout.Trace, VarListMixin):
    """
    An individual trace stored in the file, identified by run and call.

    Trace data is returned as an ``array.array()``, with an underlying
    type code specifying byte, ``int`` or ``float`` values of various precision.

    A trace may have an associated ``domain`` trace, such as time or frequency.

    .. note::

        Neither ``str`` not ``complex`` data types are supported by
        ``array.array()`` at this time.
    """

    __slots__ = ()

    @property
    def domain(self) -> Trace:
        """
        The domain of the trace
        """

        return self.run._register(self._domain)

    def __repr__(self):
        typename = self.datatype.__name__
        return f"Trace[#{self.id}, {typename}[{self.size}], {self._key_val()}]"

_psout.Trace = Trace


