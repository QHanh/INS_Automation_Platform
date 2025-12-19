#!/usr/bin/env python3
#===============================================================================
# MHRC Automation Library - Embedded Script Wrapper
#===============================================================================

"""
MHRC Automation Library - Embedded Script Wrapper

This module is used to start a user script from inside the application.
The user script may be terminated by the main application, such as by a
[Stop] button in the UI.

*** For internal application use only ***
"""

#===============================================================================
# Imports
#===============================================================================

import sys, threading, traceback

from ctypes import c_long, py_object, pythonapi
from linecache import clearcache

from .remote import Context


#===============================================================================
# UserScript
#===============================================================================

class _UserScript(threading.Thread):

    """
    A thread object used to run the user script.
    """

    def __init__(self, application, script, file="<string>"):

        """
        Constructor

        Parameters:
            application (str): application object name
            script (str): Script to execute
            file (str): Name of the script file
        """

        super().__init__()

        self._application = application
        self._script = script
        self._file = file
        self._tid = 0

    def run(self):

        """Method representing the User Script's main activity"""

        self._set_thread_id()
        self._main()

    def _set_thread_id(self):
        for tid, tobj in threading._active.items(): # pylint: disable=protected-access
            if tobj is self:
                self._tid = tid
                return
        raise AssertionError("Could not determine thread's id")

    def _main(self):
        child_globals = {
            '__name__': '__main__',
            '__file__': self._file,
            '__package__': None,
            self._application: Context._embedded(), # pylint: disable=protected-access
            }
        try:
            code = compile(self._script, self._file, 'exec')
            exec(code, child_globals)                # pylint: disable=exec-used

        except BaseException:                     # pylint: disable=broad-except
            # Report reason for failure, but don't mention our wrapper
            #
            #     File "C:\...\mhi\...\common\_script.py", line 93, in _main
            #       exec(script, module_globals)
            #
            # in the stack trace.
            etype, value, stack = sys.exc_info()
            traceback.print_exception(etype, value, stack.tb_next)

        finally:
            # Ensure any memorized file/line information is forgotten.
            clearcache()

    def _async_raise(self, exctype=KeyboardInterrupt):
        res = pythonapi.PyThreadState_SetAsyncExc(c_long(self._tid),
                                                  py_object(exctype))
        if res == 0:
            raise ValueError("Invalid thread id")
        if res != 1:
            pythonapi.PyThreadState_SetAsyncExc(c_long(self._tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def killScript(self, exctype=KeyboardInterrupt): # pylint: disable=invalid-name
        """
        Interrupt the User Script by injecting an exception into the
        thread
        """

        self._async_raise(exctype)
