#! /usr/bin/env python3

"""
Process launching and querying
"""

#===============================================================================
# Imports
#===============================================================================

import logging, os, subprocess, random
from distutils.version import LooseVersion
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

# Pywin32
from winreg import EnumKey as _EnumKey
from winreg import OpenKey as _OpenKey, CloseKey as _CloseKey
from winreg import QueryValueEx as _QueryValueEx
from winreg import HKEY_LOCAL_MACHINE as _HKLM, KEY_READ as _KEY_READ
from winreg import KEY_WOW64_32KEY as _KEY32, KEY_WOW64_64KEY as _KEY64
from winreg import REG_SZ as _REG_SZ
import ctypes, socket, struct, win32con, win32com.client


#===============================================================================
# Pywin32, socket, related window constants, structures
#===============================================================================


_AF_INET = 2
_DWORD = ctypes.c_ulong
_ERROR_NO_MORE_ITEMS = 259
_MIB_TCP_STATE_LISTEN = 2
_NULL = ""
_TCP_TABLE_BASIC_ALL = 2
_TCP_TABLE_OWNER_PID_LISTENER = 3


# pylint: disable=too-few-public-methods, missing-class-docstring, invalid-name

class MIB_TCPROW_LH(ctypes.Structure):
    _fields_ = [('dwState', _DWORD),
                ('dwLocalAddr', _DWORD),
                ('dwLocalPort', _DWORD),
                ('dwRemoteAddr', _DWORD),
                ('dwRemotePort', _DWORD)]

class MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [('dwState', _DWORD),
                ('dwLocalAddr', _DWORD),
                ('dwLocalPort', _DWORD),
                ('dwRemoteAddr', _DWORD),
                ('dwRemotePort', _DWORD),
                ('dwOwningPid', _DWORD)]

# pylint: enable=too-few-public-methods, missing-class-docstring, invalid-name

#===============================================================================
# Logging
#===============================================================================

_LOG = logging.getLogger(__name__)


#===============================================================================
# WMI Query
#===============================================================================

def _wmi():
    if not hasattr(_wmi, '_cache'):
        obj = win32com.client.GetObject('winmgmts:')
        t_i = obj._oleobj_.GetTypeInfo().GetContainingTypeLib()[0].GetTypeComp() # pylint: disable=protected-access
        flags = (t_i.Bind('wbemFlagReturnImmediately')[1].value |
                 t_i.Bind('wbemFlagForwardOnly')[1].value)
        _wmi._cache = (obj, flags)            # pylint: disable=protected-access

    return _wmi._cache                        # pylint: disable=protected-access

def _query(*props: str, where: Optional[str] = None, kind: type = tuple):

    fields = ', '.join(props)

    query = "SELECT {} FROM Win32_Process".format(fields)
    if where:
        query += " WHERE " + where
    _LOG.debug("WMI.query: %s", query)

    wmi, flags = _wmi()
    result = wmi.ExecQuery(query, iFlags=flags)

    return [kind(getattr(row, prop) for prop in props) for row in result]


#===============================================================================
# Find processes
#===============================================================================

def process_pids(*names: str) -> List[Tuple[str, int]]:

    """
    Return the process id's of any process with the given executable names.

    Application names may include the ``%`` wildcard.  For example,
    the following query might find both ``SkypeApp.exe`` and
    ``SkypeBackgroundHost.exe``::

        process_ids('skype%.exe')

    Since applications may terminate and can be started at any time,
    the returned value is obsolete immediately upon being returned.

    Parameters:
        *names (str): application filename patterns, without any path.

    Returns:
        List[tuple]: A list of process name & process id pairs
    """

    if len(names) == 1 and isinstance(names[0], (tuple, list)):
        names = names[0]

    where = None
    if names:
        where = " OR ".join("Name LIKE %r" % name for name in names)

    return _query('Name', 'ProcessId', where=where)


def is_running(app_name: str) -> bool:

    """
    Determine if there is an ``app`` process in the list of running processes.

    Application names may include the ``%`` wildcard.  For example,
    the following query might find both ``SkypeApp.exe`` and
    ``SkypeBackgroundHost.exe``::

        is_running('skype%.exe')

    Since applications may terminate and can be started at any time,
    the returned value is obsolete immediately upon being returned.

    Parameters:
        app (str): application filename, without any path.

    Returns:
        bool: `True` if a process can be found, `False` otherwise.
    """

    return len(_query('ProcessId', where='Name LIKE %r' % app_name)) > 0


#===============================================================================
# Listening Ports
#===============================================================================

def tcp_ports_in_use() -> Set[int]:
    """
    Find all TCP ports in use

    Returns:
        Set[int]: Set of all ports in use by the TCP protocol
    """

    ip_api = ctypes.windll.iphlpapi

    dw_size = _DWORD(0)
    b_order = 0        # Unordered

    # Get TcpTable dwSize value
    ip_api.GetExtendedTcpTable(_NULL, ctypes.byref(dw_size), b_order,
                               _AF_INET, _TCP_TABLE_BASIC_ALL, 0)

    # Divide the size of buffer by the size of each row to get the
    # approximate number of rows in the table.  If the header is large,
    # or there is a lot of padding, we might end up allocating an extra
    # row or two, but it is OK to have extra.
    max_rows = dw_size.value // ctypes.sizeof(MIB_TCPROW_LH)

    # pylint: disable=too-few-public-methods, missing-class-docstring, invalid-name, attribute-defined-outside-init

    class MIB_TCPTABLE(ctypes.Structure):
        _fields_ = [('dwNumEntries', _DWORD),
                    ('table', MIB_TCPROW_LH * max_rows)]

    tcp_table = MIB_TCPTABLE()
    tcp_table.dwNumEntries = 0

    # pylint: enable=too-few-public-methods, missing-class-docstring, invalid-name, attribute-defined-outside-init

    error = ip_api.GetExtendedTcpTable(ctypes.byref(tcp_table),
                                       ctypes.byref(dw_size), b_order, _AF_INET,
                                       _TCP_TABLE_BASIC_ALL, 0)

    if error:
        ports = set()
        _LOG.warning("Error getting TCP Table: %s", error)

    else:
        ports = set(socket.ntohs(row.dwLocalPort)
                    for row in tcp_table.table[:tcp_table.dwNumEntries])

    return ports


def unused_tcp_port() -> int:
    """
    Find an available TCP ports in the dynamic/private range

    Returns:
        int: an available TCP port
    """

    used_ports = tcp_ports_in_use()

    port = random.randint(49152, 65535)
    while port in used_ports:
        port = random.randint(49152, 65535)
    return port


def listener_ports_by_pid(*pid: int) -> List[Tuple[str, int, int]]:
    """
    Find all listener ports opened by processes with the given PIDs.

    Since applications may terminate and can be started at any time,
    as well as open and close ports at any time,
    the returned value is obsolete immediately upon being returned.

    Parameters:
        *pid (int): Process ids

    Returns:
        List[tuple]: a list of (addr, port, pid) tuples
    """

    # Loosely based on:
    #   "Using the WIN32 IPHelper API (Python Recipe)"
    #   http://code.activestate.com/recipes/392572/

    def addr_port(row):

        l_addr = socket.inet_ntoa(struct.pack('L', row.dwLocalAddr))
        l_port = socket.ntohs(row.dwLocalPort)

        return l_addr, l_port, row.dwOwningPid

    ip_api = ctypes.windll.iphlpapi

    dw_size = _DWORD(0)
    b_order = 0        # Unordered

    # Get TcpTable dwSize value
    ip_api.GetExtendedTcpTable(_NULL, ctypes.byref(dw_size), b_order,
                               _AF_INET, _TCP_TABLE_OWNER_PID_LISTENER, 0)

    # Divide the size of buffer by the size of each row to get the
    # approximate number of rows in the table.  If the header is large,
    # or there is a lot of padding, we might end up allocating an extra
    # row or two, but it is OK to have extra.
    max_rows = dw_size.value // ctypes.sizeof(MIB_TCPROW_OWNER_PID)

    # pylint: disable=too-few-public-methods, missing-class-docstring, invalid-name, attribute-defined-outside-init

    class MIB_TCPTABLE_OWNER_PID(ctypes.Structure):
        _fields_ = [('dwNumEntries', _DWORD),
                    ('table', MIB_TCPROW_OWNER_PID * max_rows)]

    tcp_table = MIB_TCPTABLE_OWNER_PID()
    tcp_table.dwNumEntries = 0

    # pylint: enable=too-few-public-methods, missing-class-docstring, invalid-name, attribute-defined-outside-init

    error = ip_api.GetExtendedTcpTable(ctypes.byref(tcp_table),
                                       ctypes.byref(dw_size), b_order, _AF_INET,
                                       _TCP_TABLE_OWNER_PID_LISTENER, 0)

    if error:
        ports = []
        _LOG.warning("Error getting TCP Table: %s", error)

    else:
        ports = [addr_port(row)
                 for row in tcp_table.table[:tcp_table.dwNumEntries]
                 if (row.dwState == _MIB_TCP_STATE_LISTEN and
                     row.dwOwningPid in pid)]

    return ports


def listener_ports_by_name(*names: str) -> List[Tuple[str, int, int, str]]:

    """
    Find all listener ports opened by processes with the given executable name.

    Application names may include the ``%`` wildcard.  For example,
    the following query might find both listener ports opened by both
    ``SkypeApp.exe`` and ``SkypeBackgroundHost.exe``::

        listener_ports_by_name('skype%.exe')

    Since applications may terminate and can be started at any time,
    as well as open and close ports at any time,
    the returned value is obsolete immediately upon being returned.

    Parameters:
        *names (str): application filename patterns, without any path.

    Returns:
        List[tuple]: a list of (addr, port, pid, name) tuples
    """

    name_by_pid = {pid: name for name, pid in process_pids(*names)}

    ports = [(addr, port, pid, name_by_pid[pid])
             for addr, port, pid in listener_ports_by_pid(*name_by_pid.keys())]

    return ports


#===============================================================================
# Launch processes
#===============================================================================

def _subkeys(key) -> Iterator[str]:

    i = 0
    while True:
        try:
            yield _EnumKey(key, i)
            i += 1
        except OSError as ex:
            if ex.winerror == _ERROR_NO_MORE_ITEMS: # type: ignore
                break
            raise

def _app_path(app_name: str) -> List[Dict[str, str]]:

    app_paths = []

    company_names = ['Manitoba HVDC Research Centre Inc',
                     'Manitoba Hydro International']

    for access in (_KEY32, _KEY64):     # pylint: disable=too-many-nested-blocks
        paths = {}
        for company_name in company_names:
            keyname = r'SOFTWARE\{}\{}'.format(company_name, app_name)

            try:
                key = _OpenKey(_HKLM, keyname, 0, access | _KEY_READ)
                for ver in _subkeys(key):
                    subkey = _OpenKey(key, ver)
                    try:
                        app_path = _QueryValueEx(subkey, 'AppPath')
                        if app_path[1] == _REG_SZ:
                            paths[ver] = app_path[0]
                    except FileNotFoundError:
                        pass
                    _CloseKey(subkey)
                _CloseKey(key)
            except FileNotFoundError:
                pass
        app_paths.append(paths)

    return app_paths

def _exe_path(app_name: str) -> List[Dict[str, str]]:

    exe_paths = []

    for app_paths in _app_path(app_name):
        paths = {}

        for version, path in app_paths.items():
            exe = os.path.join(path, app_name + '.exe')
            if os.path.isfile(exe):
                paths[version] = exe
            else:
                exe = os.path.join(path, app_name + version + '.exe')
                if os.path.isfile(exe):
                    paths[version] = exe

        exe_paths.append(paths)

    return exe_paths

def versions(app_name: str) -> List[Tuple[str, bool]]:
    """
    Find the installed versions of an MHI application.

    Returns:
        List[Tuple]: List of tuples of version and bit-size
    """

    versions32, versions64 = _exe_path(app_name)

    versions_all = [(version, True) for version in versions64]
    for version in versions32:
        versions_all.append((version, False))

    return versions_all


def find_exe(app_name: str,
             version: Optional[str] = None, x64: Optional[bool] = None,
             minimum: Optional[str] = None, maximum: Optional[str] = None,
             allow_alpha: bool = True, allow_beta: bool = True
             ) -> Optional[str]:

    """
    Find an MHI application executable.

    If no ``version`` is specified, the highest version available is used,
    with Alpha and Beta versions being considered the highest and second
    highest respectively.
    If no ``x64`` flag is given, a 32-bit or 64-bit version may be returned,
    with preference given to 64-bit versions.

    Parameters:
        app (str): name of the application (without any extension)
        version (str): application version number such as '4.6.3' or 'Alpha'
        x64 (bool): ``True`` for 64-bit version, ``False`` for 32-bit version
        minimum (str): The lowest allowable version, such as '5.0'
        maximum (str): The highest allowable version, such as '4.6.9'
        allow_alpha (bool): Set to False to exclude alpha versions
        allow_beta (bool): Set to False to exclude beta versions

    Returns:
        str: the path to the executable

    .. versionadded:: 2.1
        ``minimum``, ``maximum``, ``allow_alpha`` & ``allow_beta`` parameters.
    """

    versions32, versions64 = _exe_path(app_name)


    # Select the 32 or 64 bit dictionaries, or merge the two dictionaries
    if x64 is not None:
        filtered = versions64 if x64 else versions32
    else:
        filtered = dict(versions32, **versions64)

    # Filter
    if not allow_alpha:
        filtered = {ver:filtered[ver] for ver in filtered if ver != 'Alpha'}

    if not allow_beta:
        filtered = {ver:filtered[ver] for ver in filtered if ver != 'Beta'}

    if minimum:
        limit = LooseVersion(minimum)
        filtered = {ver:filtered[ver] for ver in filtered
                    if ver.isalpha() or LooseVersion(ver) >= limit}

    if maximum:
        limit = LooseVersion(maximum)
        filtered = {ver:filtered[ver] for ver in filtered
                    if ver.isalpha() or LooseVersion(ver) <= limit}


    # If an explicit version is not given, select the latest version
    # (starting with Alpha)
    if version is None:
        if 'Alpha' in filtered:
            version = 'Alpha'
        elif 'Beta' in filtered:
            version = 'Beta'
        else:
            version = max(filtered, default=None, key=LooseVersion)
            if version is None:
                return None

    return filtered.get(version, None)



def launch(*args: str, options: Dict[str, Any] = None, **kwargs):

    """
    Launch an application process.

    All ``{keyword}`` format codes in the list of ``args`` strings are
    replaced by the value in the corresponding ``options`` dictionary and/or
    ``kwargs`` key-value argument pairs.

    For example::

        launch("C:\\{dir}\\{name}.exe", "/silent:{silent}", "/title:{title!r}",
               dir="temp", name="app", silent=True, title="Hello world")

    will launch ``C:\\temp\\app.exe`` passing the arguments ``/silent:True``
    and ``/title:'Hello world'``


    Parameters:
        *args (str): the application and the arguments for the application
        options: values which may be substituted in the application arguments
        **kwargs: additional substitution values

    Returns:
        The subprocess handle

    .. table:: Special keyword arguments

        =================== ============================================
        Keyword=Value              Effect
        =================== ============================================
        ``minimize=True``   process started with ``SW_SHOWMINNOACTIVE``
        ``minimize=False``  process started with ``SW_SHOWNOACTIVATE``
        ``debug=True``             process is not started, command line printed
        =================== ============================================
    """

    if not args:
        raise ValueError("An application must be specified")

    if len(args) == 1 and isinstance(args[0], (tuple, list)):
        args = args[0]

    options = dict(options, **kwargs) if options else kwargs
    launch_args = [arg.format(**options) for arg in args]

    if options.get('debug', False):
        print("Awaiting manual launch in debugger")
        print("    args:", " ".join(launch_args[1:]))
        proc = None
    else:
        proc = _launch(launch_args, options)

    return proc

def _launch(args: List[str], options: Dict[str, Any]):

    _LOG.info("Launching %s", args[0])
    _LOG.info("    Args: %s", args[1:])

    # Ensure application crashes don't result in an Error Dialog
    # that needs to be dismissed manually
    ctypes.windll.kernel32.SetErrorMode(win32con.SEM_NOGPFAULTERRORBOX)

    # Start Up Info for the child process
    sui = subprocess.STARTUPINFO()
    minimize = options.get('minimize', None)
    minimize = options.get('launch-minimized', minimize) # Backwards compat
    if minimize is not None:
        if minimize:
            sui.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            sui.wShowWindow = win32con.SW_SHOWMINNOACTIVE
        else:
            sui.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            sui.wShowWindow = win32con.SW_SHOWNOACTIVATE

    # Launch the subprocess
    proc = subprocess.Popen(args, close_fds=True, startupinfo=sui)
    _LOG.debug("Process ID = %d", proc.pid)

    return proc


#===============================================================================
# Unit test
#===============================================================================

if __name__ == '__main__':

    # Show executables for known apps, but it is ok if they aren't installed.
    for app in ('PSCAD', 'Enerplot'):
        print(app, "=", find_exe(app))
    for app in ('PSCAD', 'Enerplot'):
        print(app, "=", find_exe(app, allow_alpha=False, allow_beta=False))
