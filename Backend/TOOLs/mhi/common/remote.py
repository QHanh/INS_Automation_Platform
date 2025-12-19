#! /usr/bin/env python3
"""
Remote method invocation from Python scripts to MHI application entities.
"""

import sys, queue, pickle, io, importlib, time, warnings, socket, threading
from typing import Any, Dict, Optional, Union, TYPE_CHECKING
from functools import wraps
from distutils.version import LooseVersion


#===============================================================================
# Window constants
#===============================================================================

_WSAEOPNOTSUPP = 10045


#===============================================================================
# Exceptions
#===============================================================================

class RemoteException(Exception):

    """Indication of an API error communicating with remote objects"""

    def __init__(self, message, *args):
        if args:
            message = message % args
        super().__init__(message)


#===============================================================================
# Remotable
#===============================================================================

class Remotable:

    """
    Base class for Remote Method Invocation (RMI) enabled objects
    """

    _identity = None # type: Dict[str, Any]
    _context = None # type: Context

    def __init__(self):
        raise RemoteException("Attempt to instantiate a Proxy object")

    def _pid(self):
        cls = self.__class__
        module = getattr(self, '_MODULE', cls.__module__)
        return module, cls.__name__, self._identity

    def __repr__(self):
        identity = ", ".join("%s=%r" % (key, val)
                             for key, val in self._identity.items())
        return "%s(%s)" % (self.__class__.__name__, identity)

    def __eq__(self, other):
        return self._pid() == other._pid()

    def __ne__(self, other):
        return self._pid() != other._pid()

    def __hash__(self):
        if '_hash' not in self.__dict__:
            keys = tuple(sorted(self._identity.keys()))
            values = tuple(self._identity[key] for key in keys) # pylint: disable=unsubscriptable-object
            self._hash = hash((keys, values)) # pylint: disable=attribute-defined-outside-init

        return self._hash

    @property
    def main(self) -> "Application":
        """
        A reference to the :class:`.Application` object that returned this
        ``Remotable`` object.
        """

        return self._context._main            # pylint: disable=protected-access


#===============================================================================
# Remote Method Invocation
#===============================================================================

class rmi_property(property):

    """
    A property which is stored in a remote object

    Apply this decorator to a property of a :class:`.Remotable` object causes
    the property access attempts to be forwarded to the remote application
    object.

    Remote properties may never be deleted.
    """

    def _fget(self) -> Any:
        """Undocumented"""

    def __init__(self, fget=None, fset=None, doc=None, name=None):
        if fget is True:
            fget = rmi_property._fget
        super().__init__(fget=fget, fset=fset, fdel=None, doc=doc)
        if doc is not None:
            self.__doc__ = doc
        if not name:
            if fget and hasattr(fget, '__name__'):
                name = fget.__name__

        if not name:
            if sys.hexversion < 0x03060000:
                raise RuntimeError("rmi_property missing name")
            warnings.warn("rmi_property missing name", stacklevel=2)

        self._key = name

    def __set_name__(self, owner, name):
        if self._key and self._key != name:
            raise AttributeError("@rmi_property name: "+name+" vs "+self._key)
        self._key = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not self.fget:
            raise AttributeError("can't get attribute %s" % self._key)
        result = instance._context._getprop(instance, self._key)
        if isinstance(result, Exception):
            raise result
        return result

    def __set__(self, instance, value):
        if not self.fset:
            raise AttributeError("can't set attribute %s" % self._key)
        if instance is not None:
            exception = instance._context._setprop(instance, self._key, value)
            if isinstance(exception, Exception):
                raise exception

    def __delete__(self, instance):
        raise AttributeError("can't delete attribute %s" % self._key)

    def __repr__(self):
        return "RemoteProperty(%r)" % self._key

    def __call__(self, fget):
        return rmi_property(fget, self.fset, fget.__doc__, fget.__name__)


#===============================================================================
# Remote Method Invocation
#===============================================================================

def rmi(method):
    """
    Remote Method Invocation

    Apply this decorator to a method of a :class:`.Remotable` object causes
    the method invocation to be forwarded to the remote application object.
    The body of the decorated method is ignored.
    """

    if isinstance(method, property):
        return rmi_property(method.fget, method.fset, method.fdel,
                            method.__doc__)

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        result = self._context._call(self, method.__name__, *args, **kwargs) # pylint: disable=protected-access
        if isinstance(result, Exception):
            exception = result
            raise exception
        return result

    return wrapper


#===============================================================================
# Application
#===============================================================================

class Application(Remotable):

    """
    A Remote Application object.

    This object represents the running application.  It implements the
    "context manager" protocol, allowing a Python script to automatically
    close the communication channel when the application object goes out of
    scope.
    """

    #-----------------------------------------------------------------------
    # Context Manager
    #-----------------------------------------------------------------------

    def __enter__(self):
        """
        Context Manager protocol

        Called when the application is used in a `with ...` statement.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager protocol

        When execution escapes the `with ...` statement, the connection
        to the application is closed.
        """

        self.close_connection()


    #-----------------------------------------------------------------------
    # Initialization
    #-----------------------------------------------------------------------

    def _initialize(self):
        pass


    #-----------------------------------------------------------------------
    # _generic command
    #-----------------------------------------------------------------------

    @rmi
    def _generic_cmd(self, cmd_id: int, lparam: int = 0, post: bool = False):
        """
        Execute a generic 'WM_COMMAND' command.

        Parameters:
            cmd_id (int): a 'word' parameter for the WM_COMMAND
            lparam (int): a 'long' parameter for the command (defaults to 0)
            post (bool): if True, uses PostMessage(), otherwise SendMessage()
        """

    #-----------------------------------------------------------------------
    # Common application functions
    #-----------------------------------------------------------------------

    @rmi_property(True, True)
    def silence(self) -> bool:
        """
        When set to `True`, silence all popup dialogs, using the dialog's
        "default" action.
        """


    def is_alive(self) -> bool:
        """
        Tests whether the application process is still running, and the
        communication socket to the application is still open.

        Returns:
            bool: ``True`` is the application communication channel is open,
            ``False`` otherwise.
        """

        return self._context.is_alive()


    @rmi
    def quit(self) -> None:
        """
        Terminate the remote application.

        Note: The local side of the socket connection to the remote
        application is not explicitly closed.  The client is responsible
        for explicitly closing the connection::

            application.quit()
            application.close_connection()

        or by using a context manager::

            with ... as application:
                # interact with the application
                #
                # application.close_connection() is automatically called
                # when the `with` statement block exits.
        """


    def close_connection(self) -> None:

        """
        Terminate connection to remote application.

        Note: The remote application will not be terminated.
        The "silence all dialog and message boxes" flag is cleared.
        """

        self.silence = False
        self._context.close()

    #-----------------------------------------------------------------------
    # Version Attribute
    #-----------------------------------------------------------------------
    @property
    def version(self) -> str:
        """Application Version"""
        raise NotImplementedError()


    #-----------------------------------------------------------------------
    # Requires
    #-----------------------------------------------------------------------

    def minimum_version(self, version: Union[str, LooseVersion]) -> bool:
        """
        Test if the remote application version is the given version or later.

        Parameters:
            version (str): The version number to test against.

        Returns:
            bool: ``True`` if the remote application version is greater than
                or equal to ``version``, ``False`` otherwise.
        """

        if not hasattr(self, '_version'):
            self._version = LooseVersion(self.version) # pylint: disable=attribute-defined-outside-init
        if self._version.vstring in ('Alpha', 'Beta'):
            return True

        if not isinstance(version, LooseVersion):
            version = LooseVersion(version)

        return self._version >= version


    def requires(self, version: str, msg: str = "Feature") -> None:
        """
        Verify the remote application is the given version or later.

        A ``NotImplementedError`` is raised if the remote application version
        is less than the required version.

        Parameters:
            version (str): The required version number.
        """

        if not self.minimum_version(version):
            msg = "{} requires application version >= {}".format(msg, version)
            raise NotImplementedError(msg)


#===============================================================================
# requires decorator
#===============================================================================

def requires(version: str):
    """
    Requires a specific application version

    Ensures the appropriate remote application version before attempting to
    invoke the function.
    """

    required_version = LooseVersion(version)

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            self.main.requires(required_version, method.__name__)
            return method(self, *args, **kwargs)
        return wrapper
    return decorator


#===============================================================================
# requires decorator
#===============================================================================

def deprecated(message="This method is deprecated"):
    """
    Flag a method as deprecated
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return method(self, *args, **kwargs)

        return wrapper

    return decorator if isinstance(message, str) else deprecated()(message)


#===============================================================================
# Context
#===============================================================================

class Context:

    """
    A Remote Context object

    This class is responsible for communications between the Python script
    and the remote application objects.

    Calls to :class:`.rmi` methods and access to :class:`.rmi_properties`
    are pickled, and sent over a communication channel.  The results of
    these operations are received from the communication channel, depickled,
    and returned to the caller.  Any exception generated by the remote
    operation is also transfered over the communication channel and raised
    locally.
    """

    _SIZE_OF_LENGTH = 4
    _EMBEDDED_SERVER = None # type: Optional[Server]
    _EMBEDDED_APPLICATION = None # type: Application

    #-----------------------------------------------------------------------
    # Factory & Constructor
    #-----------------------------------------------------------------------

    @classmethod
    def _application(cls, connect, launch, process_name=None) -> Application:

        app = None

        # Embedded?
        if cls._EMBEDDED_SERVER:
            app = cls._EMBEDDED_APPLICATION
            if app is None:
                app = cls._embedded()

        else:
            # Already running?

            from . import process      # pylint: disable=import-outside-toplevel

            if process_name and process.is_running(process_name):
                try:
                    app = connect()
                except ConnectionRefusedError:
                    pass

        # Connection to a running application succeeded?
        if app is not None:
            app.silence = True
            return app

        # No, try launching it
        return launch()

    @classmethod
    def _embedded(cls) -> Application:
        cls._EMBEDDED_APPLICATION = QueueContext(cls._EMBEDDED_SERVER)._main # pylint: disable=protected-access
        return cls._EMBEDDED_APPLICATION

    @classmethod
    def _connect(cls, host, port, timeout=5) -> Application:

        sock = socket.socket()

        if hasattr(socket, 'SIO_LOOPBACK_FAST_PATH'):
            try:
                sock.ioctl(socket.SIO_LOOPBACK_FAST_PATH, True)
            except OSError as exc:
                if exc.winerror != _WSAEOPNOTSUPP:  # type: ignore
                    raise

        ex = None
        for _ in range(timeout):
            try:
                sock.connect((host, port))
            except ConnectionRefusedError as err:
                ex = err
                time.sleep(1)
            else:
                ex = None
                break
        if ex:
            raise ex                          # pylint: disable=raising-bad-type

        context = SocketContext(sock)

        return context._main                  # pylint: disable=protected-access

    def __init__(self):
        super().__init__()

        self._pickler = Context._Pickler()
        self._unpickler = Context._Unpickler(self)

        self._thread = threading.Thread(target=self._reader, daemon=True,
                                        name='RxClient')
        self._thread.start()
        self._response = queue.Queue()

        self._main = self._getprop("SERVER", "_main")


    #-----------------------------------------------------------------------
    # RxClient
    #-----------------------------------------------------------------------

    def _reader(self):
        try:
            while self.is_alive():
                channel, msg = self._read()
                if channel:
                    self._broadcast(channel, msg)
                else:
                    self._response.put(msg)
        except OSError as ioerr:
            self._response.put(ioerr)
        except EOFError:
            pass # Can't forward EOF over connection
        finally:
            self._thread = None

    def _broadcast(self, channel, msg):
        self._main._broadcast(channel, msg)   # pylint: disable=protected-access

    #-----------------------------------------------------------------------
    # Close & Closed check
    #-----------------------------------------------------------------------

    def is_alive(self) -> bool:
        """Is a connection to the server still active?"""
        raise NotImplementedError()

    def close(self) -> None:
        """Close communication"""
        raise NotImplementedError()

    #-----------------------------------------------------------------------
    # RMI Calls & Property Set/Get
    #-----------------------------------------------------------------------

    def _call(self, rcvr, method_name, *args, **kwargs):
        msg = ("_call", rcvr, method_name, args, kwargs)
        return self._rmi(msg)

    def _getprop(self, rcvr, attr_name):
        msg = ("_getprop", rcvr, attr_name)
        return self._rmi(msg)

    def _setprop(self, rcvr, attr_name, value):
        msg = ("_setprop", rcvr, attr_name, value)
        return self._rmi(msg)

    #-----------------------------------------------------------------------
    # Write command to the remote server, and read the response
    #-----------------------------------------------------------------------

    def _rmi(self, msg):
        if not self.is_alive():
            raise OSError("Connection has been closed")

        self._write(msg)
        return self._response.get()

    def _write(self, obj):
        buf = self._pickler.dumps(obj)
        self._tx_message(buf)

    def _read(self):
        buf = self._rx_message()
        return self._unpickler.loads(buf)

    def _tx_message(self, msg):
        raise NotImplementedError("Method must be overridden")

    def _rx_message(self):
        raise NotImplementedError("Method must be overridden")


    #===========================================================================
    # Pickler
    #===========================================================================

    class _Pickler(pickle.Pickler):

        def __init__(self):
            file = io.BytesIO()
            super().__init__(file)
            self._file = file
            self.fast = True

        def persistent_id(self, obj): # pylint: disable=missing-function-docstring
            if isinstance(obj, Remotable):
                return obj._pid()             # pylint: disable=protected-access
            return None

        def dumps(self, obj):       # pylint: disable=missing-function-docstring
            self._file.seek(0)
            self.dump(obj)
            self._file.truncate()
            res = self._file.getvalue()
            return res


    #===========================================================================
    # Unpickler
    #===========================================================================

    class _Unpickler(pickle.Unpickler):

        def __init__(self, context):
            file = io.BytesIO()
            super().__init__(file)
            self._file = file
            self._context = context

        def persistent_load(self, pid): # pylint: disable=missing-function-docstring

            if isinstance(pid, tuple):
                module_name, class_name, identity = pid
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                obj = cls.__new__(cls)
                obj._identity = identity      # pylint: disable=protected-access
                obj._context = self._context  # pylint: disable=protected-access
                return obj

            raise pickle.UnpicklingError("Unsupported PID: %r" % (pid,))

        def loads(self, data):      # pylint: disable=missing-function-docstring
            self._file.seek(0)
            self._file.write(data)
            self._file.truncate()

            self._file.seek(0)
            return self.load()


#===============================================================================
# Socket Context
#===============================================================================

class SocketContext(Context):

    """
    A context object with the communication channel implemented as a TCP/IP
    socket.
    """

    _SIZE_OF_LENGTH = 4

    def __init__(self, sock):
        self._sock = sock

        # Disable Nagling
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self._rx_len = 4096
        self._rx_view = memoryview(bytearray(self._rx_len))

        super().__init__()

    #-----------------------------------------------------------------------
    # Close & Closed check
    #-----------------------------------------------------------------------

    def is_alive(self) -> bool:
        return self._sock is not None

    def close(self) -> None:
        try:
            if self._sock is None:
                raise OSError("Connection was already closed")
            self._sock.close()
        finally:
            self._sock = None

    #-----------------------------------------------------------------------
    # Send/Receive
    #-----------------------------------------------------------------------

    def _tx_message(self, msg):
        len_buf = len(msg).to_bytes(self._SIZE_OF_LENGTH, 'big')
        self._sock.sendall(len_buf)
        self._sock.sendall(msg)

    def _rx_message(self):
        msg = self._read_buffer(self._SIZE_OF_LENGTH)
        length = int.from_bytes(msg, 'big')
        msg = self._read_buffer(length)
        return msg

    def _read_buffer(self, length):

        if length > self._rx_len:
            view = memoryview(bytearray(length))
        else:
            view = self._rx_view

        index = 0
        while index < length:
            size = self._sock.recv_into(view[index:length], 0,
                                        socket.MSG_WAITALL)
            if size <= 0:
                raise EOFError("Connection closed by remote")
            index += size

        return view[:index]


#===============================================================================
# Queue Context
#===============================================================================

class QueueContext(Context):

    """
    A context object with the communication channel implemented with a Queue
    """

    def __init__(self, server):
        self._server = server
        self._queue = queue.Queue()
        super().__init__()

    #-----------------------------------------------------------------------
    # Close & Closed check
    #-----------------------------------------------------------------------

    def is_alive(self) -> bool:
        return True

    def close(self) -> None:
        pass


    #-----------------------------------------------------------------------
    # Send/Receive
    #-----------------------------------------------------------------------

    def _tx_message(self, msg):
        self._server._post(msg, self)         # pylint: disable=protected-access

    def _rx_message(self):
        msg = self._queue.get()
        return msg

    def reply(self, reply):
        """Accept a message reply, for client"""
        self._queue.put(reply)


#===============================================================================
# Typing requires complete types at the end of the module
#===============================================================================

if TYPE_CHECKING:
    from .server import Server
