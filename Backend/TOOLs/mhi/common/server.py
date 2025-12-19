#===============================================================================
# Message Server
#===============================================================================

"""
Automation Server
"""

#===============================================================================
# Imports
#===============================================================================

import logging, queue, threading, pickle, io, socket

from socket import IPPROTO_TCP, TCP_NODELAY
from select import select as _select
from typing import Dict, Optional, Set

from .remote import RemoteException, Context, Application
from ._script import _UserScript


#===============================================================================
# Logging
#===============================================================================

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.WARNING)


#===============================================================================
# Server
#===============================================================================

class Server:                     # pylint: disable=too-many-instance-attributes
    """
    Automation Server
    """

    def __init__(self, main, idle_kick=None):
        super().__init__()

        self._main = main
        self._pickler = Server._Pickler()
        self._unpickler = Server._Unpickler(main)
        self._queue = queue.Queue()
        self._server = None
        self._user_script = None

        try:
            import embed # type: ignore # pylint: disable=import-error,import-outside-toplevel
            idle_kick = embed.idle_kick
            in_progress = embed.in_progress
        except ModuleNotFoundError:
            in_progress = object()

        self._idle_kick = idle_kick
        self._in_progress = in_progress


    def run_script(self, application: str, script: str, file: str = "<string>"):
        """Execute an internal automation user script"""
        if self._user_script:
            raise ValueError("Already running script")
        self._user_script = _UserScript(application, script, file)
        self._user_script.start()
        return self._script_running

    def _script_running(self) -> bool:
        if self._user_script:
            if not self._user_script.isAlive():
                self._user_script.join()
                self._user_script = None
        return self._user_script is not None

    def kill_script(self) -> None:
        """Forcefully abort a running internal automation user script"""
        user_script = self._user_script
        if user_script:
            user_script.killScript()

    def start_server(self, port: int = 54321, host: str = 'localhost'):
        """Begin a listen server for automation"""
        self._start_server(port, host)
        return self._post

    def _start_server(self, port: int, host: str = 'localhost') -> None:
        Context._EMBEDDED_SERVER = self       # pylint: disable=protected-access
        self._server = MessageServer(self, self._post, port, host)
        self._server.start()

    def stop_server(self) -> None:
        """Terminate the automation listen server"""
        self._server.stop()
        self._server = None
        Context._EMBEDDED_SERVER = None       # pylint: disable=protected-access

    def _post(self, msg: bytes, client) -> None:
        self._queue.put((msg, client))
        if self._idle_kick:
            self._idle_kick()

    def poll(self) -> int:
        """Check for request in automation queue"""
        size = self._queue.qsize()
        if size > 0:
            msg, client = self._queue.get()
            if client is not None:
                self._process(msg, client)
        return size

    def poll_loop(self) -> None:    # pylint: disable=missing-function-docstring
        """Process automation requests forever"""
        while True:
            msg, client = self._queue.get()
            if client is None:
                break
            self._process(msg, client)

    def _process(self, msg: bytes, client) -> None:
        try:
            cmd = self._unpickler.loads(msg)
            response = self._dispatch(cmd, client)
            if response is self._in_progress:
                _LOG.debug("Command in progress")
                reply = None
            else:
                response = None, response
                reply = self._pickler.dumps(response)
        except Exception as ex:                   # pylint: disable=broad-except
            _LOG.exception("Unpickling, dispatching or pickling error!")
            response = None, ex
            reply = self._pickler.dumps(response)

        if reply:
            try:
                client.reply(reply)
            except Exception as ex:               # pylint: disable=broad-except
                _LOG.exception("Exception replying to client!")

    def post(self, client, response, channel=None):
        """Post a delayed reply or subscription event to a client"""
        try:
            response = channel, response
            reply = self._pickler.dumps(response)
        except Exception as ex:                   # pylint: disable=broad-except
            _LOG.exception("Pickling error!")
            reply = self._pickler.dumps(ex)

        try:
            return client.reply(reply)
        except Exception as ex:                   # pylint: disable=broad-except
            _LOG.exception("Exception posting to client!")

        return False


    def _dispatch(self, cmd, client):
        response = None

        try:
            _LOG.info("Command: %r", cmd)
            action, rcvr, name = cmd[:3]
            if rcvr == "SERVER":
                rcvr = self

            if action == "_call":
                response = self._call(client, rcvr, name, cmd[3], cmd[4])
            elif action == "_getprop":
                response = self._getprop(rcvr, name)
            elif action == "_setprop":
                response = self._setprop(rcvr, name, cmd[3])
            else:
                response = RemoteException("Unknown action '%s'", action)

        except Exception as exception:            # pylint: disable=broad-except
            response = exception

        _LOG.info("Response: %r", response)
        return response


    @staticmethod
    def _call(client, rcvr, name, args, kwargs):
        method = getattr(rcvr, name, None)
        if method is None:
            return RemoteException("Unknown method %s.%s(...)",
                                   rcvr.__class__.__name__, name)
        if not callable(method):
            return RemoteException("Not a method %s.%s",
                                   rcvr.__class__.__name__, name)

        return method(client, *args, **kwargs)

    @staticmethod
    def _getprop(rcvr, name):
        return getattr(rcvr, name)

    @staticmethod
    def _setprop(rcvr, name, value):
        return setattr(rcvr, name, value)

    def _get_main_application(self) -> Application:
        return self._main

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
            if obj:
                cls = obj.__class__
                module = cls.__module__
                if module.startswith("mhi_"):
                    module = "mhi." + module[4:]
                    state = getattr(obj, '__dict__', None)
                    if state is None:
                        state = {key: getattr(obj, key) for key in dir(obj)
                                 if not key.startswith("_")}
                        state = {key: val for key, val in state.items()
                                 if not callable(val)}
                    pid = (module, cls.__name__, state)
                    return pid

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

        _MAIN = "MAIN"

        def __init__(self, main):
            file = io.BytesIO()
            super().__init__(file)
            self._file = file
            self._main = main

        def persistent_load(self, pid): # pylint: disable=missing-function-docstring
            if pid == self._MAIN:
                return self._main
            if isinstance(pid, tuple):
                module_name, class_name, identity = pid
                if module_name.startswith("mhi."):
                    module_name = "mhi_" + module_name[4:]
                cls = self.find_class(module_name, class_name)
                return cls(**identity)
            raise pickle.UnpicklingError("Unsupported PID: %r" % (pid,))

        def loads(self, data):      # pylint: disable=missing-function-docstring
            self._file.seek(0)
            self._file.write(data)
            self._file.truncate()

            self._file.seek(0)
            return self.load()



#===============================================================================
# Message Server
#===============================================================================

class MessageServer:              # pylint: disable=too-many-instance-attributes

    """A multi-client message server

    The Message Server opens a listener socket on the given port, and
    spawns a thread which manages that port.

    The thread will accept new incoming connections, receive messages
    sent from those connections and pass them to a message processor.
    It expects to receive replies from the processor, which it will
    return over the connection.

    The processor is expected to accept 2 arguments, the message and
    the connection it was received from.  The processor is expected to
    enqueue this for processing in yet another thread::

        def processor(msg:bytes, client):
            processing_queue.put((msg, client))

    When the message has been processed and a response has been created,
    the response should be passed to the client for transmission::

        client.reply(response)
    """

    # Using Optional[type] requires assert self._thing is not None everywhere
    # So we'll add typing at the class level, and type: ignore assignments to
    # None.

    _tickle = None # type: socket.socket
    _thread = None # type: threading.Thread

    #-----------------------------------------------------------------------
    # Constructor
    #-----------------------------------------------------------------------

    def __init__(self, application, processor, port: int, address='localhost'):

        self._application = application
        self._processor = processor
        self._address = (address, port)

        self._thread = None   # type: ignore
        self._tickle = None   # type: ignore

        self._rlist = set()   # type: Set[socket.socket]
        self._wlist = set()   # type: Set[socket.socket]

        self._clients = {}    # type: Dict[socket.socket, MessageServer._Connection]

        self._running = False

    #-----------------------------------------------------------------------
    # Start/Stop server
    #-----------------------------------------------------------------------

    def start(self) -> None:

        """Start the message server thread."""

        if not self._running:
            self._running = True
            self._thread = threading.Thread(name="Message Server", target=self._run)
            self._thread.start()


    def stop(self) -> None:

        """Kill the message server thread."""

        _LOG.debug("Stopping server ...")
        if self._running:
            self._running = False
            self._tickle.send(b'x')

            thread = self._thread
            self._thread = None     # type: ignore
            if thread:
                _LOG.debug("Joining server thread ...")
                thread.join()
                _LOG.info("Server thread joined - server stopped")


    #-----------------------------------------------------------------------
    # Server Thread
    #-----------------------------------------------------------------------

    def _run(self) -> None:                  # pylint: disable=too-many-branches

        _LOG.info("Listening for connections on %r", self._address)

        pair = socket.socketpair()
        with socket.socket() as listener, pair[0] as wakeup, pair[1] as self._tickle:

            if hasattr(socket, 'SIO_LOOPBACK_FAST_PATH'):
                try:
                    listener.ioctl(socket.SIO_LOOPBACK_FAST_PATH, True)
                    _LOG.info("Listener - LOOPBACK_FAST_PATH supported")
                except OSError as exc:
                    WSAEOPNOTSUPP = 10045         # pylint: disable=invalid-name
                    if exc.winerror != WSAEOPNOTSUPP:  # type: ignore
                        raise
                    _LOG.info("Listener - LOOPBACK_FAST_PATH not supported")
            else:
                _LOG.info("Listener - LOOPBACK_FAST_PATH not defined")

            listener.setblocking(False)
            listener.bind(self._address)
            listener.listen()

            self._rlist = {listener, wakeup}
            self._wlist = set()

            while self._running:
                rlist, wlist, xlist = _select(self._rlist, self._wlist,
                                              self._rlist)

                for sock in wlist:
                    self._write(sock)

                for sock in rlist:
                    if sock is listener:
                        self._accept(listener)
                    elif sock is wakeup:
                        wakeup.recv(1)
                    else:
                        self._read(sock)

                for sock in xlist:
                    self._close(sock)

        _LOG.info("Listener closed")
        self._tickle = None           # type: ignore

        # Close any open client connections - we can't service them anymore
        for sock in self._rlist:
            try:
                sock.close()
            except Exception:                     # pylint: disable=broad-except
                pass

        self._rlist.clear()
        self._wlist.clear()
        self._clients.clear()

    #-----------------------------------------------------------------------
    # Accept incoming connection
    #-----------------------------------------------------------------------

    def _accept(self, listener: socket.socket) -> None:
        sock, addr = listener.accept()
        sock.setblocking(False)
        sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1) # Disable Nagling
        _LOG.info("Accepted connection from %r", addr)

        self._rlist.add(sock)
        self._clients[sock] = MessageServer._Connection(self, sock)

    #-----------------------------------------------------------------------
    # Read incoming messages from client socket via client connection
    #-----------------------------------------------------------------------

    def _read(self, sock: socket.socket) -> None:
        try:
            client = self._clients[sock]
            if not client._read():            # pylint: disable=protected-access
                self._close(sock)
        except Exception as ex:                   # pylint: disable=broad-except
            _LOG.info("Read failed: %r", ex)
            self._close(sock)

    def _rx(self, msg, connection) -> None:
        self._processor(msg, connection)

    #-----------------------------------------------------------------------
    # Write outgoing messages to client socket from client connection
    #-----------------------------------------------------------------------

    def _write(self, sock: socket.socket) -> None:
        client = self._clients[sock]
        try:
            client._tx()                      # pylint: disable=protected-access
        except queue.Empty:
            self._wlist.remove(client._sock)  # pylint: disable=protected-access
        except Exception as ex:                   # pylint: disable=broad-except
            _LOG.info("Write failed: %r", ex)

    def _writable(self, sock) -> None:
        self._wlist.add(sock)
        self._tickle.send(b'x')

    #-----------------------------------------------------------------------
    # Close client socket/connection
    #-----------------------------------------------------------------------

    def _close(self, sock: socket.socket) -> None:
        _LOG.warning("Closed connection from %r", sock.getpeername())

        if sock in self._rlist:
            self._rlist.remove(sock)
        if sock in self._wlist:
            self._wlist.remove(sock)

        client = self._clients.pop(sock, None)

        try:
            sock.close()
        except OSError as ex:
            _LOG.info("Close failed: %r", ex)

        if client:
            client._open = False              # pylint: disable=protected-access


    #===========================================================================
    # Connection
    #===========================================================================

    class _Connection: # pylint: disable=too-few-public-methods,too-many-instance-attributes

        """A connection to a remote client.

        The connection object is used to buffer messages sent from/to the
        client, accumulating the message bytes into a temporary buffer until the
        complete message has been received, and sending message bytes from the
        transmit queue in as large of chucks as the transmit socket will accept.

        Messages are defined as an array of bytes.  The connection adds the
        length of the message to the start of the buffer just before
        transmission, and removes the length from the block of received
        messages.
        """

        SIZE_OF_LENGTH = 4
        _COMMON_LENGTH = 1024

        #-----------------------------------------------------------------------
        # Constructor
        #-----------------------------------------------------------------------

        def __init__(self, server, sock):
            self._server = server
            self._sock = sock

            self._input = None
            self._in_idx = 0
            self._in_length = 0
            self._length_buf = bytearray(self.SIZE_OF_LENGTH)
            self._common_buf = memoryview(bytearray(self._COMMON_LENGTH))

            self._tx_queue = queue.Queue()
            self._output = None
            self._out_idx = 0
            self._out_length = 0

            self._input_reset()
            self._open = True

        #-----------------------------------------------------------------------
        # Message reception from remote client
        #-----------------------------------------------------------------------

        def _input_reset(self) -> None:
            self._in_idx = 0
            self._in_length = self.SIZE_OF_LENGTH
            self._input = self._length_buf

        def _read(self) -> bool:
            chunk = self._sock.recv(self._in_length - self._in_idx)

            if chunk:
                length = len(chunk)
                self._input[self._in_idx:self._in_idx + length] = chunk
                self._in_idx += length

                if self._in_idx == self.SIZE_OF_LENGTH:
                    self._in_length += int.from_bytes(self._input, 'big')
                    if self._in_length < self._COMMON_LENGTH:
                        self._input = self._common_buf
                    else:
                        self._input = memoryview(bytearray(self._in_length))
                if self._in_idx == self._in_length:
                    self._rx(self._input[self.SIZE_OF_LENGTH:])
                    self._input_reset()
                return True

            return False

        def _rx(self, msg: memoryview) -> None:
            self._server._rx(bytes(msg), self) # pylint: disable=protected-access

        #-----------------------------------------------------------------------
        # Message transmission to remote client
        #-----------------------------------------------------------------------

        def reply(self, reply: bytes) -> bool:

            """Transmit a reply message to remote client"""

            if self._open:
                self._send(reply)
            return self._open

        def _output_reset(self) -> None:
            self._output = None
            self._out_idx = 0
            self._out_length = 0

        def _send(self, reply: bytes) -> None:
            msg = len(reply).to_bytes(self.SIZE_OF_LENGTH, 'big') + reply
            self._tx_queue.put(msg)
            if self._output is None:
                self._server._writable(self._sock) # pylint: disable=protected-access

        def _tx(self) -> None:
            if self._output is None:
                self._output = memoryview(self._tx_queue.get_nowait())
                self._out_idx = 0
                self._out_length = len(self._output)

            size = self._sock.send(self._output[self._out_idx:])
            self._out_idx += size
            if self._out_idx == self._out_length:
                self._output_reset()
